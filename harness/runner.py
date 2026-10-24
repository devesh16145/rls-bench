"""Run a candidate policy file against a task's tests (spec §6.2)."""

from __future__ import annotations

import json
import time

import psycopg

from harness import db
from harness.checks import compare, normalise_rows
from harness.models import Observation, Task, TaskResult, Test, TestResult
from harness.sqlparse import FormatError, check_candidate, extract_sql_block

HARNESS_VERSION = "3"  # bump when grading semantics change; stored samples are then regraded
APPLY_TIMEOUT = "10s"
TEST_TIMEOUT = "5s"


def _error_text(exc: psycopg.Error) -> str:
    first = str(exc).strip().splitlines()
    return first[0] if first else type(exc).__name__


SEQUENCES_SQL = """
select format('%I.%I', schemaname, sequencename), coalesce(last_value, start_value), last_value is not null
from pg_sequences
where schemaname in ('public', 'storage')
order by 1
"""


def _sequence_state(conn: psycopg.Connection) -> list[tuple[str, int, bool]]:
    return [tuple(r) for r in conn.execute(SEQUENCES_SQL).fetchall()]  # type: ignore[misc]


def _run_test(conn: psycopg.Connection, test: Test, sequences: list[tuple[str, int, bool]] | None = None) -> Observation:
    try:
        with conn.transaction(force_rollback=True):
            with conn.cursor() as cur:
                # sequences ignore rollback; reset them so every test sees the same ids
                for name, value, called in sequences or []:
                    cur.execute("select setval(%s::regclass, %s, %s)", [name, value, called])
                cur.execute(f"set local role {test.actor.role}")
                cur.execute(
                    "select set_config('request.jwt.claims', %s, true)",
                    [json.dumps(test.actor.jwt_claims(), sort_keys=True)],
                )
                cur.execute(f"set local statement_timeout = '{TEST_TIMEOUT}'")
                cur.execute(test.query)
                # multi-statement tests are judged on the last statement's result
                while cur.nextset():
                    pass
                if cur.description is not None:
                    rows = normalise_rows(cur.fetchall())
                    return Observation(rows=rows, rowcount=len(rows))
                return Observation(rowcount=cur.rowcount)
    except psycopg.Error as exc:
        return Observation(sqlstate=exc.sqlstate or "XX000", message=_error_text(exc))


def run_candidate(task: Task, candidate_sql: str) -> TaskResult:
    """Apply plain candidate SQL to a fresh copy of the task database and run every test."""
    started = time.monotonic()
    result = TaskResult(task_id=task.id, passed=False)
    try:
        check_candidate(candidate_sql)
    except FormatError as exc:
        result.format_error = str(exc)
        result.duration_ms = int((time.monotonic() - started) * 1000)
        return result

    with db.scratch_database() as uri, db.connect(uri) as conn:
        conn.execute(task.schema_sql)
        conn.execute(task.seed_sql)
        try:
            with conn.transaction():
                conn.execute(f"set local statement_timeout = '{APPLY_TIMEOUT}'")
                if candidate_sql.strip():
                    conn.execute(candidate_sql)
        except psycopg.Error as exc:
            result.apply_error = f"{exc.sqlstate}: {_error_text(exc)}"
            result.duration_ms = int((time.monotonic() - started) * 1000)
            return result

        sequences = _sequence_state(conn)
        for test in task.tests:
            obs = _run_test(conn, test, sequences)
            passed, leak, block = compare(test.expect, obs)
            result.tests.append(
                TestResult(
                    name=test.name,
                    passed=passed,
                    expected=test.expect.model_dump(exclude_none=True),
                    observed=obs,
                    leak=leak,
                    block=block,
                )
            )

    result.passed = all(t.passed for t in result.tests)
    result.leak = any(t.leak for t in result.tests)
    result.block = any(t.block for t in result.tests)
    result.duration_ms = int((time.monotonic() - started) * 1000)
    return result


def run_completion(task: Task, completion: str) -> TaskResult:
    """Grade a raw model completion: extract the ```sql block, then run it."""
    try:
        sql = extract_sql_block(completion)
    except FormatError as exc:
        return TaskResult(task_id=task.id, passed=False, format_error=str(exc))
    return run_candidate(task, sql)


def task_tables(task: Task) -> list[str]:
    """Public tables the task's schema creates, plus any extra_tables it declares."""
    with db.scratch_database() as uri, db.connect(uri) as conn:
        conn.execute(task.schema_sql)
        rows = conn.execute(
            "select tablename from pg_tables where schemaname = 'public' order by tablename"
        ).fetchall()
    return [f"public.{r[0]}" for r in rows] + list(task.meta.extra_tables)
