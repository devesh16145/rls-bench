"""Build SFT data by rejection sampling (spec §8.1).

For each train task: sample N candidates from a strong open model, keep the ones that pass every
test, dedupe by normalised SQL, keep at most K per task, and add the reference solution. Only
tasks in the frozen train split are ever used; dev and test tasks are refused.

Raw samples (every completion with its grade) are appended to data/sft_raw.jsonl; the training
file is rewritten from them as data/sft.jsonl.
"""

from __future__ import annotations

import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Callable

import httpx
import typer

from eval import openrouter
from eval.prompts import build_messages, prompt_hash
from harness import split as splitmod
from harness.db import ROOT
from harness.models import Task
from harness.runner import run_completion
from harness.sqlparse import extract_sql_block, split_statements

TASKS_DIR = ROOT / "tasks"
RAW_PATH = ROOT / "data" / "sft_raw.jsonl"
SFT_PATH = ROOT / "data" / "sft.jsonl"
DEFAULT_MODEL = "deepseek/deepseek-v4.1-flash-1017"
TEMPERATURE = 0.8
INDEX_OFFSET = 1000  # keeps SFT sample indices apart from baseline indices in the cache
TYPICAL_OUTPUT_TOKENS = 3000
CHARS_PER_TOKEN = 4

app = typer.Typer(add_completion=False)


def train_tasks(limit: int | None = None) -> list[Task]:
    split = splitmod.load()
    ids = sorted(split["train"])
    if limit is not None:
        ids = ids[:limit]
    tasks = [Task.load(next(TASKS_DIR.glob(f"{tid}-*"))) for tid in ids]
    held_out = set(split["dev"]) | set(split["test"])
    assert not any(t.id in held_out for t in tasks), "dev/test task leaked into SFT data"
    return tasks


def normalise_sql(sql: str) -> str:
    """Comment-free, whitespace-collapsed, lowercase statements: the dedupe key."""
    return ";\n".join(re.sub(r"\s+", " ", s).strip().lower() for s in split_statements(sql))


def estimate(tasks: list[Task], samples: int, model: str, max_tokens: int) -> dict[str, Any]:
    info = openrouter.model_info(model)
    price_in = float(info["pricing"]["prompt"])
    price_out = float(info["pricing"]["completion"])
    n = len(tasks) * samples
    input_tokens = sum(sum(len(m["content"]) for m in build_messages(t)) // CHARS_PER_TOKEN for t in tasks) * samples
    return {
        "model": model,
        "tasks": len(tasks),
        "samples": n,
        "typical_usd": input_tokens * price_in + n * min(TYPICAL_OUTPUT_TOKENS, max_tokens) * price_out,
        "worst_usd": input_tokens * price_in + n * max_tokens * price_out,
    }


def _assistant(sql: str) -> str:
    return f"```sql\n{sql.strip()}\n```"


def rebuild_sft(max_keep: int, log: Callable[[str], None] = print) -> dict[str, Any]:
    """Rewrite data/sft.jsonl from the raw samples plus each task's reference solution."""
    held_out = set(splitmod.load()["dev"]) | set(splitmod.load()["test"])
    raw = [json.loads(line) for line in RAW_PATH.read_text().splitlines()] if RAW_PATH.exists() else []
    by_task: dict[str, list[dict[str, Any]]] = {}
    for r in raw:
        by_task.setdefault(r["task_id"], []).append(r)
    rows, stats = [], {}
    for tid in sorted(by_task):
        assert tid not in held_out, f"{tid} is not a train task"
        task = Task.load(next(TASKS_DIR.glob(f"{tid}-*")))
        messages = build_messages(task)
        seen = {normalise_sql(task.solution_sql)}
        rows.append({"task_id": tid, "source": "reference", "messages": messages + [{"role": "assistant", "content": _assistant(task.solution_sql)}]})
        kept = 0
        passed = [r for r in sorted(by_task[tid], key=lambda r: r["index"]) if r["passed"]]
        for r in passed:
            if kept >= max_keep:
                break
            sql = extract_sql_block(r["completion"])
            key = normalise_sql(sql)
            if key in seen:
                continue
            seen.add(key)
            rows.append({"task_id": tid, "source": r["model"], "messages": messages + [{"role": "assistant", "content": _assistant(sql)}]})
            kept += 1
        stats[tid] = {"samples": len(by_task[tid]), "passed": len(passed), "kept": kept}
    SFT_PATH.parent.mkdir(parents=True, exist_ok=True)
    SFT_PATH.write_text("".join(json.dumps(r) + "\n" for r in rows))
    log(f"wrote {SFT_PATH}: {len(rows)} examples over {len(stats)} tasks")
    return {"examples": len(rows), "per_task": stats}


def sample(tasks: list[Task], *, model: str, samples: int, max_tokens: int, max_spend: float,
           concurrency: int = 4, log: Callable[[str], None] = print) -> dict[str, Any]:
    """Sample, grade and append raw rows. Skips samples already recorded; stops at max_spend."""
    done = set()
    if RAW_PATH.exists():
        for line in RAW_PATH.read_text().splitlines():
            r = json.loads(line)
            done.add((r["task_id"], r["index"], r["prompt_hash"], r["model"]))
    jobs = []
    for t in tasks:
        messages = build_messages(t)
        ph = prompt_hash(messages)
        for i in range(samples):
            idx = INDEX_OFFSET + i
            if (t.id, idx, ph, model) not in done:
                jobs.append((t, messages, ph, idx))
    log(f"{len(jobs)} samples to run ({len(tasks) * samples - len(jobs)} already recorded)")
    spent, graded, stopped = 0.0, 0, False
    RAW_PATH.parent.mkdir(parents=True, exist_ok=True)
    with httpx.Client(timeout=600) as client, ThreadPoolExecutor(max_workers=concurrency) as pool:
        futures = {}
        queue = list(jobs)

        def submit() -> None:
            t, messages, ph, idx = queue.pop(0)
            fut = pool.submit(openrouter.complete, model, messages, prompt_hash=ph, temperature=TEMPERATURE,
                              index=idx, max_tokens=max_tokens, send_temperature=True, client=client)
            futures[fut] = (t, ph, idx)

        while queue and len(futures) < concurrency:
            submit()
        while futures:
            fut = next(as_completed(futures))
            t, ph, idx = futures.pop(fut)
            completion = fut.result()
            if not completion.cached:
                spent += completion.cost_usd
            result = run_completion(t, completion.text)
            with RAW_PATH.open("a") as f:
                f.write(json.dumps({
                    "task_id": t.id, "index": idx, "model": model, "prompt_hash": ph, "temperature": TEMPERATURE,
                    "finish_reason": completion.finish_reason, "cost_usd": completion.cost_usd,
                    "passed": result.passed, "leak": result.leak, "completion": completion.text,
                }) + "\n")
            graded += 1
            if graded % 20 == 0 or not queue:
                log(f"  [{graded}/{len(jobs)}] spend ${spent:.2f}")
            if spent >= max_spend and queue and not stopped:
                stopped = True
                log(f"spend cap ${max_spend:.2f} reached; not submitting {len(queue)} remaining samples")
                queue.clear()
            while queue and len(futures) < concurrency:
                submit()
    return {"graded": graded, "spent_usd": spent, "stopped_at_cap": stopped}


@app.command()
def main(
    limit: int = typer.Option(None, help="Only the first N train tasks (sorted by id), e.g. 5 for a dry run."),
    samples: int = typer.Option(16, help="Candidates per task."),
    max_keep: int = typer.Option(6, help="Distinct passing candidates kept per task (plus the reference)."),
    model: str = typer.Option(DEFAULT_MODEL),
    max_tokens: int = typer.Option(16000),
    max_spend: float = typer.Option(20.0),
    estimate_only: bool = typer.Option(False, "--estimate", help="Print the cost estimate and exit."),
    yes: bool = typer.Option(False, "--yes", help="Confirm the spend."),
) -> None:
    tasks = train_tasks(limit)
    e = estimate(tasks, samples, model, max_tokens)
    typer.echo(f"{e['model']}: {e['samples']} samples over {e['tasks']} train tasks; "
               f"typical ${e['typical_usd']:.2f}, worst case ${e['worst_usd']:.2f}")
    if estimate_only:
        return
    if not yes:
        raise typer.BadParameter("this spends money: check the estimate, then pass --yes")
    out = sample(tasks, model=model, samples=samples, max_tokens=max_tokens, max_spend=max_spend, log=typer.echo)
    typer.echo(json.dumps(out))
    rebuild_sft(max_keep, log=typer.echo)


if __name__ == "__main__":
    app()
