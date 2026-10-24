"""Pydantic models for every file format and result the harness produces."""

from __future__ import annotations

import datetime as dt
import re
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

from harness.client import ClientCall

RULE_RE = re.compile(r"^R(\d+)\.", re.MULTILINE)


class Actor(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: Literal["anon", "authenticated", "service_role"]
    sub: str | None = None
    claims: dict[str, Any] = Field(default_factory=dict)

    def jwt_claims(self) -> dict[str, Any]:
        claims: dict[str, Any] = {"role": self.role}
        if self.sub is not None:
            claims["sub"] = self.sub
        claims.update(self.claims)
        return claims


class Expectation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rows: list[list[Any]] | None = None
    count: int | None = None
    affected: int | None = None
    error: str | None = None
    denied: bool | None = None

    @model_validator(mode="after")
    def exactly_one(self) -> "Expectation":
        set_fields = [k for k, v in self.model_dump().items() if v is not None]
        if len(set_fields) != 1:
            raise ValueError(f"expectation needs exactly one of rows/count/affected/error/denied, got {set_fields}")
        if self.denied is False:
            raise ValueError("denied must be true when present")
        return self

    @property
    def kind(self) -> str:
        return next(k for k, v in self.model_dump().items() if v is not None)


class Test(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    name: str
    covers: list[str]
    actor: Actor = Field(alias="as")
    sql: str | None = None
    client: ClientCall | None = None
    expect: Expectation

    @model_validator(mode="after")
    def sql_or_client(self) -> "Test":
        if (self.sql is None) == (self.client is None):
            raise ValueError(f"{self.name}: give exactly one of sql or client")
        return self

    @property
    def query(self) -> str:
        return self.sql if self.sql is not None else self.client.to_sql()  # type: ignore[union-attr]


class TaskMeta(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    title: str
    tier: Literal[1, 2, 3]
    tags: list[str] = Field(default_factory=list)
    traps: list[str] = Field(default_factory=list)
    extra_tables: list[str] = Field(default_factory=list)
    fixture_notes: list[str] = Field(default_factory=list)
    verified: bool
    author: str
    created: dt.date
    canary: str


class Task(BaseModel):
    meta: TaskMeta
    path: Path
    schema_sql: str
    seed_sql: str
    requirement: str
    solution_sql: str
    tests: list[Test]
    trap_sql: dict[str, str]

    @property
    def id(self) -> str:
        return self.meta.id

    @property
    def rule_ids(self) -> list[str]:
        return [f"R{n}" for n in RULE_RE.findall(self.requirement)]

    @classmethod
    def load(cls, path: Path) -> "Task":
        path = Path(path)
        meta = TaskMeta.model_validate(yaml.safe_load((path / "task.yaml").read_text()))
        raw_tests = yaml.safe_load((path / "tests.yaml").read_text()) or []
        traps_dir = path / "traps"
        trap_sql = {p.stem: p.read_text() for p in sorted(traps_dir.glob("*.sql"))} if traps_dir.exists() else {}
        return cls(
            meta=meta,
            path=path,
            schema_sql=(path / "schema.sql").read_text(),
            seed_sql=(path / "seed.sql").read_text(),
            requirement=(path / "requirement.md").read_text(),
            solution_sql=(path / "solution.sql").read_text(),
            tests=[Test.model_validate(t) for t in raw_tests],
            trap_sql=trap_sql,
        )


class Observation(BaseModel):
    rows: list[list[Any]] | None = None
    rowcount: int | None = None
    sqlstate: str | None = None
    message: str | None = None

    @property
    def errored(self) -> bool:
        return self.sqlstate is not None


class TestResult(BaseModel):
    name: str
    passed: bool
    expected: dict[str, Any]
    observed: Observation
    leak: bool = False
    block: bool = False


class TaskResult(BaseModel):
    task_id: str
    passed: bool
    tests: list[TestResult] = Field(default_factory=list)
    apply_error: str | None = None
    format_error: str | None = None
    leak: bool = False
    block: bool = False
    duration_ms: int = 0


class CheckResult(BaseModel):
    name: str
    ok: bool
    detail: str = ""
