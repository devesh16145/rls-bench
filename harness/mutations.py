"""Task validation: the reference must pass and known-bad candidates must fail (spec §6.3)."""

from __future__ import annotations

import re

from harness.models import CheckResult, Task, TaskResult
from harness.runner import run_candidate, task_tables

ORDER_BY_RE = re.compile(r"\border\s+by\b", re.IGNORECASE)


def allow_all_sql(tables: list[str]) -> str:
    lines = []
    for t in tables:
        lines.append(f"alter table {t} enable row level security;")
        lines.append(f"create policy rlsbench_allow_all on {t} for all to public using (true) with check (true);")
    return "\n".join(lines)


def deny_all_sql(tables: list[str]) -> str:
    return "\n".join(f"alter table {t} enable row level security;" for t in tables)


def _failing(result: TaskResult) -> str:
    if result.format_error:
        return f"format error: {result.format_error}"
    if result.apply_error:
        return f"apply error: {result.apply_error}"
    names = [t.name for t in result.tests if not t.passed]
    return ", ".join(names) if names else "all tests passed"


def _fingerprint(result: TaskResult) -> list[tuple[str, dict]]:
    """What grading depends on. Returned rows count only for rows/count expectations, so
    `returning *` over columns with random defaults (e.g. storage.objects.id) is not noise."""
    out = []
    for t in result.tests:
        obs = t.observed.model_dump()
        if "rows" not in t.expected and "count" not in t.expected:
            obs["rows"] = None
        out.append((t.name, obs))
    return out + [
        ("_apply", {"apply_error": result.apply_error, "format_error": result.format_error})
    ]


def check_coverage(task: Task) -> CheckResult:
    rules = task.rule_ids
    cited = {c for t in task.tests for c in t.covers}
    uncovered = [r for r in rules if r not in cited]
    unknown = sorted(c for c in cited if c not in rules)
    problems = []
    if not rules:
        problems.append("requirement.md has no R1., R2., ... rules")
    if uncovered:
        problems.append(f"uncovered rules: {', '.join(uncovered)}")
    if unknown:
        problems.append(f"tests cite unknown rules: {', '.join(unknown)}")
    empty = [t.name for t in task.tests if not t.covers]
    if empty:
        problems.append(f"tests with empty covers: {', '.join(empty)}")
    return CheckResult(name="coverage", ok=not problems, detail="; ".join(problems) or f"{len(rules)} rules covered")


def check_structure(task: Task) -> CheckResult:
    problems = []
    roles = {t.actor.role for t in task.tests}
    if "anon" not in roles:
        problems.append("no anon test")
    if "service_role" not in roles:
        problems.append("no service_role test")
    if task.meta.tier >= 2 and not task.meta.traps:
        problems.append("tier 2-3 task lists no traps")
    if task.meta.canary not in task.requirement:
        problems.append("canary missing from requirement.md")
    if not task.meta.canary.startswith("RLSBENCH-CANARY-"):
        problems.append("canary has wrong prefix")
    if not task.path.name.startswith(task.meta.id + "-"):
        problems.append(f"directory {task.path.name} does not start with id {task.meta.id}")
    names = [t.name for t in task.tests]
    dupes = sorted({n for n in names if names.count(n) > 1})
    if dupes:
        problems.append(f"duplicate test names: {', '.join(dupes)}")
    for t in task.tests:
        if t.expect.rows is not None and len(t.expect.rows) > 1 and not ORDER_BY_RE.search(t.query):
            problems.append(f"{t.name}: multi-row expectation without order by")
        if t.actor.role == "authenticated" and t.actor.sub is None:
            problems.append(f"{t.name}: authenticated actor without sub")
    return CheckResult(name="structure", ok=not problems, detail="; ".join(problems) or "ok")


def validate_task(task: Task) -> tuple[list[CheckResult], TaskResult]:
    """Run every check; return the results and the reference run (for the review card)."""
    checks: list[CheckResult] = []
    tables = task_tables(task)

    reference = run_candidate(task, task.solution_sql)
    checks.append(CheckResult(name="reference", ok=reference.passed, detail=_failing(reference)))

    empty = run_candidate(task, "")
    checks.append(CheckResult(name="no-policy", ok=not empty.passed, detail=_failing(empty)))

    allow = run_candidate(task, allow_all_sql(tables))
    checks.append(CheckResult(name="allow-all", ok=not allow.passed, detail=_failing(allow)))

    deny = run_candidate(task, deny_all_sql(tables))
    deny_blocks = any(t.block for t in deny.tests)
    checks.append(
        CheckResult(name="deny-all", ok=not deny.passed and deny_blocks, detail=_failing(deny))
    )

    again = run_candidate(task, task.solution_sql)
    same = _fingerprint(reference) == _fingerprint(again)
    checks.append(CheckResult(name="deterministic", ok=same, detail="identical" if same else "results differ"))

    checks.append(check_coverage(task))
    checks.append(check_structure(task))

    trap_problems, trap_details = [], []
    for trap in task.meta.traps:
        sql = task.trap_sql.get(trap)
        if sql is None:
            trap_problems.append(f"{trap}: traps/{trap}.sql missing")
            continue
        res = run_candidate(task, sql)
        if res.format_error or res.apply_error:
            trap_problems.append(f"{trap}: must apply cleanly ({_failing(res)})")
        elif res.passed:
            trap_problems.append(f"{trap}: planted trap passes every test")
        else:
            trap_details.append(f"{trap} caught by {_failing(res)}")
    extra = sorted(set(task.trap_sql) - set(task.meta.traps))
    if extra:
        trap_problems.append(f"trap files not listed in task.yaml: {', '.join(extra)}")
    checks.append(
        CheckResult(
            name="traps",
            ok=not trap_problems,
            detail="; ".join(trap_problems + trap_details) or "no traps listed",
        )
    )
    return checks, reference
