import pytest

from harness.sqlparse import FormatError, check_candidate, extract_sql_block, split_statements


def test_split_respects_dollar_quotes_and_comments():
    sql = """
    -- a comment; with a semicolon
    create function f() returns int language sql as $$ select 1; $$;
    /* block; comment */ create policy p on t for select using (x = 'a;b');
    """
    stmts = split_statements(sql)
    assert len(stmts) == 2
    assert stmts[0].startswith("create function")
    assert "'a;b'" in stmts[1]


def test_policies_for_writes_are_allowed():
    sql = """
    alter table public.notes enable row level security;
    create policy a on notes for insert to authenticated with check (true);
    create policy b on notes for update using (true);
    create policy c on notes for delete using (true);
    """
    assert len(check_candidate(sql)) == 4


@pytest.mark.parametrize(
    "stmt",
    [
        "insert into notes values (1)",
        "update notes set body = 'x'",
        "delete from notes",
        "drop table notes",
        "alter table notes add column x int",
        "alter table notes disable row level security",
        "truncate notes",
        "grant service_role to authenticated",
        "alter role authenticated bypassrls",
        "create or replace function auth.uid() returns uuid language sql as $$ select null::uuid $$",
        "create trigger t before insert on storage.objects for each row execute function f()",
        "do $$ begin perform 1; end $$",
        "set role service_role",
    ],
)
def test_forbidden_statements(stmt):
    with pytest.raises(FormatError):
        check_candidate(stmt + ";")


def test_function_bodies_may_contain_writes():
    sql = "create function public.f() returns trigger language plpgsql as $f$ begin delete from x; return new; end $f$;"
    assert len(check_candidate(sql)) == 1


def test_extract_first_sql_block():
    text = "Here:\n```sql\nselect 1;\n```\nand\n```sql\nselect 2;\n```"
    assert extract_sql_block(text).strip() == "select 1;"
    with pytest.raises(FormatError):
        extract_sql_block("no block here")
