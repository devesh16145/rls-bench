"""The single fixed prompt template (spec §7.1). Changing it invalidates every cached result."""

from __future__ import annotations

import hashlib

from harness import db
from harness.models import Task

SYSTEM = (
    "You are a senior database engineer. Write Supabase Row Level Security for the schema and rules below. "
    "Available: `auth.uid()`, `auth.jwt()`, `auth.role()`, roles `anon`, `authenticated`, `service_role` "
    "(bypasses RLS). Output exactly one ```sql block containing only: `alter table ... enable row level "
    "security`, `create policy`, helper `create function`, `create trigger`, `create view`, and "
    "grants/revokes. Do not modify existing tables or data. No explanation outside the block."
)


def seed_shape(task: Task) -> str:
    """Row counts per table after seeding: the shape of the data, never the rows."""
    with db.scratch_database() as uri, db.connect(uri) as conn:
        conn.execute(task.schema_sql)
        conn.execute(task.seed_sql)
        tables = conn.execute(
            """
            select schemaname || '.' || relname
            from pg_stat_user_tables
            where schemaname in ('public', 'auth', 'storage')
            order by schemaname = 'public' desc, 1
            """
        ).fetchall()
        lines = []
        for (name,) in tables:
            n = conn.execute(f"select count(*) from {name}").fetchone()[0]
            if n:
                lines.append(f"- {name}: {n} rows")
    return "\n".join(lines)


def build_user(task: Task) -> str:
    return (
        "## Schema\n\n```sql\n"
        + task.schema_sql.strip()
        + "\n```\n\nSupabase's `auth.users` and `storage.buckets` / `storage.objects` tables already exist.\n\n"
        + "## Seed data (row counts only)\n\n"
        + seed_shape(task)
        + "\n\n## Access rules\n\n"
        + task.requirement.strip()
        + "\n"
    )


def build_messages(task: Task) -> list[dict[str, str]]:
    return [{"role": "system", "content": SYSTEM}, {"role": "user", "content": build_user(task)}]


def prompt_hash(messages: list[dict[str, str]]) -> str:
    h = hashlib.sha256()
    for m in messages:
        h.update(m["role"].encode())
        h.update(b"\0")
        h.update(m["content"].encode())
        h.update(b"\0")
    return h.hexdigest()[:16]
