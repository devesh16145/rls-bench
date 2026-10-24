"""Render supabase-js style calls into the SQL PostgREST runs for them.

PostgREST wraps writes in a CTE and selects from it; the RLS consequences are the same as the
plain statements rendered here:
- `.insert(...).select()` → `insert ... returning *`: the new row must also pass the SELECT policies.
- `.upsert(...)` → `insert ... on conflict (...) do update set ...`: needs INSERT, and for existing
  rows UPDATE (and SELECT) policies too.
- `.update(...).eq(...)` / `.delete().eq(...)` → filtered update/delete, optionally `returning *`.
"""

from __future__ import annotations

import json
import re
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

IDENT_RE = re.compile(r"^[a-z_][a-z0-9_]*(\.[a-z_][a-z0-9_]*)?$")


def literal(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return repr(value)
    if isinstance(value, str):
        return "'" + value.replace("'", "''") + "'"
    if isinstance(value, (dict, list)):
        return literal(json.dumps(value, sort_keys=True)) + "::jsonb"
    raise TypeError(f"unsupported literal {value!r}")


def _ident(name: str) -> str:
    if not IDENT_RE.match(name):
        raise ValueError(f"bad identifier {name!r}")
    return name


class ClientCall(BaseModel):
    model_config = ConfigDict(extra="forbid")

    op: Literal["select", "insert", "upsert", "update", "delete"]
    table: str
    values: dict[str, Any] | list[dict[str, Any]] | None = None
    match: dict[str, Any] = Field(default_factory=dict)
    on_conflict: list[str] | None = None
    returning: bool = False  # supabase-js `.select()` after a write
    columns: str = "*"
    order: str | None = None

    @model_validator(mode="after")
    def check(self) -> "ClientCall":
        _ident(self.table)
        if self.op in {"insert", "upsert", "update"} and not self.values:
            raise ValueError(f"{self.op} needs values")
        if self.op == "upsert" and not self.on_conflict:
            raise ValueError("upsert needs on_conflict")
        if self.op in {"update", "delete"} and not self.match:
            raise ValueError(f"{self.op} needs match (supabase-js refuses unfiltered writes)")
        return self

    def _where(self) -> str:
        if not self.match:
            return ""
        return " where " + " and ".join(f"{_ident(k)} = {literal(v)}" for k, v in self.match.items())

    def to_sql(self) -> str:
        t = self.table
        ret = " returning *" if self.returning else ""
        if self.op == "select":
            order = f" order by {self.order}" if self.order else ""
            return f"select {self.columns} from {t}{self._where()}{order}"
        if self.op in {"insert", "upsert"}:
            rows = self.values if isinstance(self.values, list) else [self.values]
            cols = list(rows[0])
            for r in rows:
                if list(r) != cols:
                    raise ValueError("all rows must have the same columns")
            values = ", ".join("(" + ", ".join(literal(r[c]) for c in cols) + ")" for r in rows)
            sql = f"insert into {t} ({', '.join(_ident(c) for c in cols)}) values {values}"
            if self.op == "upsert":
                conflict = [_ident(c) for c in self.on_conflict or []]
                sets = [f"{c} = excluded.{c}" for c in cols if c not in conflict]
                sql += f" on conflict ({', '.join(conflict)}) do update set {', '.join(sets)}"
            return sql + ret
        if self.op == "update":
            assert isinstance(self.values, dict)
            sets = ", ".join(f"{_ident(k)} = {literal(v)}" for k, v in self.values.items())
            return f"update {t} set {sets}{self._where()}{ret}"
        return f"delete from {t}{self._where()}{ret}"
