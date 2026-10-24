"""`rls` command line."""

from __future__ import annotations

import json
from pathlib import Path

import typer

from harness import db
from harness.card import render
from harness.models import Task
from harness.mutations import validate_task
from harness.runner import run_candidate, run_completion

app = typer.Typer(no_args_is_help=True, add_completion=False)
db_app = typer.Typer(no_args_is_help=True, help="Start or stop the Postgres server.")
app.add_typer(db_app, name="db")

TASKS_DIR = db.ROOT / "tasks"


def _all_tasks() -> list[Path]:
    return sorted(p for p in TASKS_DIR.glob("T*") if (p / "task.yaml").exists())


def _resolve(paths: list[Path], all_: bool) -> list[Path]:
    if all_:
        return _all_tasks()
    if not paths:
        raise typer.BadParameter("give task directories or --all")
    return paths


@db_app.command("up")
def db_up() -> None:
    """Start Postgres (docker → pgserver → pg_ctl) and build the template database."""
    db.up()
    backend = (db.STATE_DIR / "uri").read_text().splitlines()[0]
    typer.echo(f"postgres up ({backend}); template {db.TEMPLATE_DB} ready")


@db_app.command("down")
def db_down() -> None:
    """Stop Postgres."""
    db.down()
    typer.echo("postgres stopped")


@app.command()
def validate(
    paths: list[Path] = typer.Argument(None),
    all_: bool = typer.Option(False, "--all", help="Validate every task under tasks/."),
) -> None:
    """Run the mutation checks on one or more tasks."""
    failed = 0
    for path in _resolve(paths, all_):
        task = Task.load(path)
        checks, _ = validate_task(task)
        ok = all(c.ok for c in checks)
        failed += not ok
        typer.echo(f"{'PASS' if ok else 'FAIL'} {path.name}")
        for c in checks:
            typer.echo(f"  {'✓' if c.ok else '✗'} {c.name}: {c.detail}")
    raise typer.Exit(code=1 if failed else 0)


@app.command()
def run(
    task_path: Path,
    candidate: Path,
    completion: bool = typer.Option(False, help="Treat the file as a raw model completion (extract the ```sql block)."),
    as_json: bool = typer.Option(False, "--json", help="Print the full TaskResult as JSON."),
) -> None:
    """Run one candidate SQL file against a task and print per-test results."""
    task = Task.load(task_path)
    text = candidate.read_text()
    result = run_completion(task, text) if completion else run_candidate(task, text)
    if as_json:
        typer.echo(result.model_dump_json(indent=2))
    else:
        typer.echo(
            f"{task.id}: {'PASS' if result.passed else 'FAIL'}  leak={result.leak} block={result.block} "
            f"{result.duration_ms}ms"
        )
        if result.format_error:
            typer.echo(f"  format error: {result.format_error}")
        if result.apply_error:
            typer.echo(f"  apply error: {result.apply_error}")
        for t in result.tests:
            mark = "✓" if t.passed else ("✗ LEAK" if t.leak else "✗ BLOCK" if t.block else "✗")
            line = f"  {mark} {t.name}"
            if not t.passed:
                line += f"  expected {json.dumps(t.expected)} observed {t.observed.model_dump_json(exclude_none=True)}"
            typer.echo(line)
    raise typer.Exit(code=0 if result.passed else 1)


def _eval_tasks(include_unverified: bool, only: list[str] | None = None) -> list[Task]:
    tasks = [Task.load(p) for p in _all_tasks()]
    if only:
        tasks = [t for t in tasks if t.id in only]
    if not include_unverified:
        tasks = [t for t in tasks if t.meta.verified]
    if not tasks:
        raise typer.BadParameter("no verified tasks (set verified: true after review, or pass --include-unverified)")
    return tasks


def _reasoning_options(reasoning: str, max_tokens: int | None) -> tuple[str, int]:
    from eval.run_baselines import REASONING_SETTINGS

    if reasoning not in REASONING_SETTINGS:
        raise typer.BadParameter(f"--reasoning must be one of {sorted(REASONING_SETTINGS)}")
    return reasoning, max_tokens or (16000 if reasoning == "default" else 4096)


@app.command()
def estimate(
    model: list[str] = typer.Option(..., "--model", help="OpenRouter model id; repeatable."),
    k: int = typer.Option(5, help="Samples at temperature 0.7 per task (plus one at temperature 0)."),
    max_tokens: int = typer.Option(None, help="Completion cap per sample, reasoning included (default 16000, or 4096 with --reasoning off)."),
    reasoning: str = typer.Option("default", help="Reasoning setting: default (provider default) or off."),
    include_unverified: bool = typer.Option(False, help="Also count tasks not yet verified."),
    task: list[str] = typer.Option(None, "--task", help="Limit to these task ids (e.g. T011); repeatable."),
) -> None:
    """Print the cost estimate for a baseline run from live OpenRouter prices. Spends nothing."""
    from eval.run_baselines import estimate as estimate_cost

    reasoning, max_tokens = _reasoning_options(reasoning, max_tokens)
    tasks = _eval_tasks(include_unverified, task)
    total_typ = total_worst = 0.0
    for m in model:
        e = estimate_cost(m, tasks, k, max_tokens, reasoning)
        total_typ += e["typical_usd"]
        total_worst += e["worst_usd"]
        typer.echo(
            f"{m}: {e['samples']} samples over {e['tasks']} tasks; "
            f"${e['price_in_per_m']:.2f}/M in, ${e['price_out_per_m']:.2f}/M out; "
            f"~{e['input_tokens']:,} input tokens; "
            f"typical ${e['typical_usd']:.2f} (≈{e['typical_output_tokens']:,} output tokens), "
            f"worst case ${e['worst_usd']:.2f} (every sample hits {max_tokens:,} tokens); "
            f"temperature honoured: {e['honours_temperature']}; reasoning {e['reasoning']} (optional: {e['reasoning_optional']})"
        )
    typer.echo(f"TOTAL: typical ${total_typ:.2f}, worst case ${total_worst:.2f}")


@app.command("eval")
def eval_cmd(
    model: str = typer.Option(..., "--model", help="OpenRouter model id."),
    k: int = typer.Option(5),
    max_tokens: int = typer.Option(None),
    reasoning: str = typer.Option("default", help="default or off"),
    max_spend: float = typer.Option(20.0, help="Stop submitting new requests at this spend (USD)."),
    concurrency: int = typer.Option(4),
    include_unverified: bool = typer.Option(False),
    task: list[str] = typer.Option(None, "--task", help="Limit to these task ids (e.g. T011); repeatable."),
    yes: bool = typer.Option(False, "--yes", help="Confirm the spend shown by `rls estimate`."),
) -> None:
    """Baseline one model: sample, grade, append raw lines to results/baselines/."""
    from eval.run_baselines import run_model

    if not yes:
        raise typer.BadParameter("this spends money: run `rls estimate` first, then pass --yes")
    reasoning, max_tokens = _reasoning_options(reasoning, max_tokens)
    tasks = _eval_tasks(include_unverified, task)
    summary = run_model(model, tasks, k=k, max_tokens=max_tokens, max_spend=max_spend, concurrency=concurrency, reasoning=reasoning, log=typer.echo)
    typer.echo(json.dumps(summary, indent=2))


@app.command("regrade")
def regrade_cmd(
    model: list[str] = typer.Option(None, "--model", help="Model ids to regrade; default all."),
) -> None:
    """Re-grade stored completions against the current tests (free; appends, never rewrites)."""
    from eval.run_baselines import BASELINES_DIR, model_slug, regrade

    tasks = [Task.load(p) for p in _all_tasks()]
    paths = [BASELINES_DIR / f"{model_slug(m)}.jsonl" for m in model] if model else sorted(BASELINES_DIR.glob("*.jsonl"))
    for path in paths:
        regrade(path, tasks, log=typer.echo)


@app.command()
def summarize() -> None:
    """Rebuild results/summary.json from the raw lines in results/baselines/."""
    from eval.metrics import summarize as build_summary

    out = db.ROOT / "results" / "summary.json"
    summary = build_summary(db.ROOT / "results" / "baselines", out)
    for slug, m in summary["models"].items():
        p1, leak = m["pass_at_1"], m["leak_rate"]
        p5 = m["pass_at_5"]["rate"]
        typer.echo(
            f"{slug}: pass@1 {p1['rate']:.0%} [{p1['lo']:.0%}–{p1['hi']:.0%}] n={p1['n']}  "
            f"pass@5 {'–' if p5 is None else f'{p5:.0%}'}  leak {leak['rate']:.0%} [{leak['lo']:.0%}–{leak['hi']:.0%}]"
        )
    typer.echo(f"wrote {out.relative_to(db.ROOT)}")


@app.command()
def split(freeze: bool = typer.Option(False, "--freeze", help="Write tasks/split.json (only once, ever).")) -> None:
    """Show the frozen train/dev/test split, or freeze it with --freeze."""
    from harness import split as splitmod

    if freeze:
        result = splitmod.freeze([Task.load(p) for p in _all_tasks()])
        typer.echo(f"froze {splitmod.SPLIT_PATH.relative_to(db.ROOT)}")
    else:
        result = splitmod.load()
    typer.echo(f"counts {result['counts']} per tier {result['per_tier']} seed {result['seed']}")


@app.command()
def card(
    paths: list[Path] = typer.Argument(None),
    all_: bool = typer.Option(False, "--all"),
) -> None:
    """Validate and print the owner's review card for each task."""
    for path in _resolve(paths, all_):
        task = Task.load(path)
        checks, _ = validate_task(task)
        typer.echo(render(task, checks))
        typer.echo("")


if __name__ == "__main__":
    app()
