"""Review card the owner reads before setting verified: true (spec §9)."""

from __future__ import annotations

import json

from harness.models import CheckResult, Task

EXPECTED_FAIL = {"no-policy", "allow-all", "deny-all"}


def _as(test) -> str:
    a = test.actor
    who = a.role if a.sub is None else f"{a.role}:{a.sub[-2:]}"
    if a.claims:
        who += f" +claims{json.dumps(a.claims, sort_keys=True)}"
    return who


def render(task: Task, checks: list[CheckResult]) -> str:
    m = task.meta
    out: list[str] = []
    out.append("=" * 100)
    out.append(
        f"TASK {m.id} — {m.title} — tier {m.tier} — traps: {', '.join(m.traps) or 'none'} — verified: {m.verified}"
    )
    out.append(f"tags: {', '.join(m.tags)}")
    out.append("")
    out.append("REQUIREMENT (verbatim)")
    out.append(task.requirement.rstrip())
    out.append("")
    out.append("TESTS (name → as → expect → covers)")
    for t in task.tests:
        expect = json.dumps(t.expect.model_dump(exclude_none=True))
        out.append(f"  {t.name} → {_as(t)} → {expect} → {', '.join(t.covers)}")
        prefix = "[supabase-js] " if t.client is not None else ""
        out.append(f"      {prefix}{' '.join(t.query.split())}")
    out.append("")
    out.append("SOLUTION (verbatim)")
    out.append(task.solution_sql.rstrip())
    out.append("")
    parts = []
    for c in checks:
        if c.name in EXPECTED_FAIL:
            parts.append(f"{c.name} {'✗(expected)' if c.ok else '✓ PROBLEM'}")
        else:
            parts.append(f"{c.name} {'✓' if c.ok else '✗'}")
    out.append("VALIDATE: " + "  ".join(parts))
    for c in checks:
        if c.name in EXPECTED_FAIL:
            out.append(f"  {c.name}: fails on {c.detail}")
        elif not c.ok or c.name in {"coverage", "traps"}:
            out.append(f"  {c.name}: {c.detail}")
    out.append("FIXTURE EDGE ROWS (check these exist in seed.sql):")
    for note in m.fixture_notes or ["(none listed)"]:
        out.append(f"  - {note}")
    return "\n".join(out)
