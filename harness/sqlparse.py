"""Extract the model's SQL block and enforce the statement allowlist (spec §5.1)."""

from __future__ import annotations

import re

FENCE_RE = re.compile(r"```[ \t]*sql[ \t]*\n(.*?)```", re.DOTALL | re.IGNORECASE)
DOLLAR_TAG_RE = re.compile(r"\$([A-Za-z_][A-Za-z_0-9]*)?\$")

PROTECTED_SCHEMAS = {"auth", "storage", "pg_catalog", "information_schema"}

ALLOWED = [
    re.compile(r"^alter table (if exists )?(only )?[\w\".]+ (enable|force) row level security$"),
    re.compile(r"^create (or replace )?function "),
    re.compile(r"^create (or replace )?(constraint )?trigger "),
    re.compile(r"^(create|drop|alter) policy "),
    re.compile(r"^create (or replace )?(temp |temporary )?view "),
    re.compile(r"^alter view (if exists )?[\w\".]+ set \("),
    re.compile(r"^create schema "),
    re.compile(r"^(grant|revoke) .* on "),
    re.compile(r"^create (unique )?index "),
    re.compile(r"^comment on "),
]

OBJECT_NAME_RE = re.compile(
    r"^create (?:or replace )?(?:function|(?:temp |temporary )?view|(?:constraint )?trigger)\s+(?:if not exists\s+)?\"?(\w+)\"?\s*\."
)
TRIGGER_TABLE_RE = re.compile(r"\bon\s+\"?(\w+)\"?\s*\.")


class FormatError(ValueError):
    pass


def extract_sql_block(completion: str) -> str:
    """Return the first ```sql block of a model completion, or raise FormatError."""
    match = FENCE_RE.search(completion)
    if not match:
        raise FormatError("no ```sql block")
    return match.group(1)


def split_statements(sql: str) -> list[str]:
    """Split on top-level semicolons, respecting quotes, dollar quotes and comments.

    Comments are dropped from the returned statements.
    """
    statements: list[str] = []
    buf: list[str] = []
    i, n = 0, len(sql)
    while i < n:
        ch = sql[i]
        if sql.startswith("--", i):
            end = sql.find("\n", i)
            i = n if end == -1 else end
            continue
        if sql.startswith("/*", i):
            end = sql.find("*/", i + 2)
            i = n if end == -1 else end + 2
            buf.append(" ")
            continue
        if ch in ("'", '"'):
            j = i + 1
            while j < n:
                if sql[j] == ch:
                    if j + 1 < n and sql[j + 1] == ch:
                        j += 2
                        continue
                    break
                j += 1
            buf.append(sql[i : j + 1])
            i = j + 1
            continue
        if ch == "$":
            tag = DOLLAR_TAG_RE.match(sql, i)
            if tag:
                end = sql.find(tag.group(0), tag.end())
                stop = n if end == -1 else end + len(tag.group(0))
                buf.append(sql[i:stop])
                i = stop
                continue
        if ch == ";":
            stmt = "".join(buf).strip()
            if stmt:
                statements.append(stmt)
            buf = []
            i += 1
            continue
        buf.append(ch)
        i += 1
    tail = "".join(buf).strip()
    if tail:
        statements.append(tail)
    return statements


def _normalise(stmt: str) -> str:
    return re.sub(r"\s+", " ", stmt).strip().lower()


def check_statement(stmt: str) -> None:
    norm = _normalise(stmt)
    if not any(p.match(norm) for p in ALLOWED):
        raise FormatError(f"statement not allowed: {norm[:80]}")
    name = OBJECT_NAME_RE.match(norm)
    if name and name.group(1) in PROTECTED_SCHEMAS:
        raise FormatError(f"may not create objects in schema {name.group(1)}: {norm[:80]}")
    if re.match(r"^create (or replace )?(constraint )?trigger ", norm):
        on = TRIGGER_TABLE_RE.search(norm)
        if on and on.group(1) in PROTECTED_SCHEMAS:
            raise FormatError(f"may not add triggers in schema {on.group(1)}: {norm[:80]}")


def check_candidate(sql: str) -> list[str]:
    """Return the statements if all are allowed; raise FormatError otherwise."""
    statements = split_statements(sql)
    for stmt in statements:
        check_statement(stmt)
    return statements
