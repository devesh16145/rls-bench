"""Compare an observation to an expectation and classify failures as leak or block."""

from __future__ import annotations

import datetime as dt
import decimal
import uuid
from collections import Counter
from typing import Any

from harness.models import Expectation, Observation

# deliberate refusals: privilege/RLS error, raise exception, check violation (common errcode for custom raises).
# Unique/foreign-key violations are not accepted: they can hide a real hole behind an accidental conflict.
DENIED_SQLSTATES = {"42501", "P0001", "23514"}


def normalise_value(value: Any) -> Any:
    if value is None or isinstance(value, (bool, str)):
        return value
    if isinstance(value, int):
        return value
    if isinstance(value, (float, decimal.Decimal)):
        d = decimal.Decimal(str(value))
        return int(d) if d == d.to_integral_value() else str(d.normalize())
    if isinstance(value, uuid.UUID):
        return str(value)
    if isinstance(value, (dt.datetime, dt.date, dt.time)):
        return value.isoformat()
    if isinstance(value, (list, tuple)):
        return [normalise_value(v) for v in value]
    if isinstance(value, dict):
        return {k: normalise_value(v) for k, v in value.items()}
    return str(value)


def normalise_rows(rows: list[list[Any]] | list[tuple[Any, ...]]) -> list[list[Any]]:
    return [[normalise_value(v) for v in row] for row in rows]


def _key(row: list[Any]) -> str:
    return repr(row)


def _single_number(rows: list[list[Any]]) -> int | None:
    if len(rows) == 1 and len(rows[0]) == 1 and isinstance(rows[0][0], int) and not isinstance(rows[0][0], bool):
        return rows[0][0]
    return None


def compare(expect: Expectation, obs: Observation) -> tuple[bool, bool, bool]:
    """Return (passed, leak, block)."""
    kind = expect.kind

    if kind == "rows":
        wanted = normalise_rows(expect.rows or [])
        if obs.errored:
            return False, False, bool(wanted)
        got = obs.rows or []
        if got == wanted:
            return True, False, False
        # select count(*) style: compare the number
        want_n, got_n = _single_number(wanted), _single_number(got)
        if want_n is not None and got_n is not None:
            return False, got_n > want_n, got_n < want_n
        extra = Counter(map(_key, got)) - Counter(map(_key, wanted))
        missing = Counter(map(_key, wanted)) - Counter(map(_key, got))
        return False, bool(extra), bool(missing)

    if kind == "count":
        want = expect.count or 0
        if obs.errored:
            return False, False, want > 0
        got = len(obs.rows) if obs.rows is not None else (obs.rowcount or 0)
        return got == want, got > want, got < want

    if kind == "affected":
        want = expect.affected or 0
        if obs.errored:
            return False, False, want > 0
        got = obs.rowcount or 0
        return got == want, got > want, got < want

    if kind == "error":
        if obs.sqlstate == expect.error:
            return True, False, False
        succeeded = not obs.errored and (obs.rowcount or 0) > 0
        return False, succeeded, False

    if kind == "denied":
        if obs.errored:
            return obs.sqlstate in DENIED_SQLSTATES, False, False
        if (obs.rowcount or 0) == 0:
            return True, False, False
        return False, True, False

    raise ValueError(f"unknown expectation kind {kind}")
