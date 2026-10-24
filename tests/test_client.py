import pytest

from harness.client import ClientCall


def test_insert_with_select_renders_returning():
    c = ClientCall(op="insert", table="notes", values={"user_id": "u", "body": "it's"}, returning=True)
    assert c.to_sql() == "insert into notes (user_id, body) values ('u', 'it''s') returning *"


def test_upsert_updates_non_conflict_columns():
    c = ClientCall(op="upsert", table="profiles", values={"id": "u", "bio": None}, on_conflict=["id"])
    assert c.to_sql() == "insert into profiles (id, bio) values ('u', null) on conflict (id) do update set bio = excluded.bio"


def test_update_and_delete_need_filters():
    with pytest.raises(ValueError):
        ClientCall(op="delete", table="notes")
    c = ClientCall(op="update", table="notes", values={"body": "x"}, match={"id": 1}, returning=True)
    assert c.to_sql() == "update notes set body = 'x' where id = 1 returning *"


def test_bad_identifier_rejected():
    with pytest.raises(ValueError):
        ClientCall(op="select", table="notes; drop table x")
