import json

from harness import db


def _query(sql: str, role: str | None = None, claims: dict | None = None):
    with db.scratch_database() as uri, db.connect(uri) as conn:
        with conn.transaction(force_rollback=True):
            if role:
                conn.execute(f"set local role {role}")
            if claims is not None:
                conn.execute("select set_config('request.jwt.claims', %s, true)", [json.dumps(claims)])
            return conn.execute(sql).fetchone()


def test_auth_functions_read_claims():
    claims = {"role": "authenticated", "sub": "00000000-0000-0000-0000-000000000007", "app": "x"}
    uid, role, jwt = _query("select auth.uid()::text, auth.role(), auth.jwt() ->> 'app'", "authenticated", claims)
    assert uid == claims["sub"]
    assert role == "authenticated"
    assert jwt == "x"


def test_auth_uid_null_without_claims():
    assert _query("select auth.uid()", "anon", {"role": "anon"}) == (None,)
    assert _query("select auth.uid(), auth.jwt()") == (None, None)


def test_service_role_bypasses_rls_on_storage():
    with db.scratch_database() as uri, db.connect(uri) as conn:
        conn.execute("insert into storage.buckets (id, name) values ('b', 'b')")
        conn.execute("insert into storage.objects (bucket_id, name) values ('b', 'x/y.txt')")
        counts = {}
        for role in ("anon", "authenticated", "service_role"):
            with conn.transaction(force_rollback=True):
                conn.execute(f"set local role {role}")
                counts[role] = conn.execute("select count(*) from storage.objects").fetchone()[0]
    assert counts == {"anon": 0, "authenticated": 0, "service_role": 1}


def test_storage_path_helpers():
    assert _query("select storage.foldername('a/b/c.txt'), storage.filename('a/b/c.txt')") == (["a", "b"], "c.txt")
