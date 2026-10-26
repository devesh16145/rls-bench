"""SFT data from open models sampled on Tinker, merged with the OpenRouter (DeepSeek) data (spec §8.2, version 3).

`sample`: N answers per train task from a Tinker base model with its reasoning-off template, graded by the
harness, appended to data/sft_raw_tinker.jsonl in the same record shape as data/sft_raw.jsonl.
`rebuild`: data/sft_v3.jsonl = per train task, the reference plus up to K distinct passing answers drawn
round-robin from every raw source (so the mix is as diverse as the sources allow).
`dev-set`: data/sft_dev.jsonl rebuilt from the dev tasks' references and every passing dev-task sample in
the baseline and leaderboard files (DeepSeek, Kimi), for the held-out loss.
"""

from __future__ import annotations

import datetime as dt
import json
import warnings
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import typer

warnings.filterwarnings("ignore", message=r'Field "model_')

from eval.prompts import build_messages, prompt_hash  # noqa: E402
from harness import split as splitmod  # noqa: E402
from harness.db import ROOT  # noqa: E402
from harness.models import Task  # noqa: E402
from harness.runner import run_completion  # noqa: E402
from harness.sqlparse import extract_sql_block  # noqa: E402
from train.build_sft import RAW_PATH, TASKS_DIR, _assistant, normalise_sql, train_tasks  # noqa: E402
from train.leaderboard import MODELS as LEADERBOARD_RENDERERS  # noqa: E402
from train.prices import price  # noqa: E402
from train.sft_tinker import load_tinker_key, make_renderer  # noqa: E402

RAW_TINKER_PATH = ROOT / "data" / "sft_raw_tinker.jsonl"
SFT_V3_PATH = ROOT / "data" / "sft_v3.jsonl"
DEV_PATH = ROOT / "data" / "sft_dev.jsonl"
DEV_SOURCES = (ROOT / "results" / "baselines" / "deepseek__deepseek-v4.1-flash-1017.jsonl",
               ROOT / "results" / "tinker_eval" / "Kimi-K2.6@reasoning-off.jsonl")
TEMPERATURE = 0.8
INDEX_OFFSET = 2000  # keeps these indices apart from baseline (0..) and OpenRouter SFT (1000..) samples
TYPICAL_COMPLETION_TOKENS = 700

app = typer.Typer(add_completion=False)


@app.callback()
def _cli() -> None:
    """Subcommands below."""


def estimate(tasks: list[Task], renderer, samples: int, max_tokens: int, model: str) -> dict[str, Any]:
    p = price(model)
    prefill = sum(renderer.build_generation_prompt(build_messages(t)).length for t in tasks) * samples
    n = len(tasks) * samples
    return {"model": model, "tasks": len(tasks), "samples": n, "prefill_tokens": prefill,
            "typical_usd": round((prefill * p["prefill"] + n * min(TYPICAL_COMPLETION_TOKENS, max_tokens) * p["sample"]) / 1e6, 3),
            "worst_usd": round((prefill * p["prefill"] + n * max_tokens * p["sample"]) / 1e6, 3)}


@app.command()
def sample(model: str = typer.Option("moonshotai/Kimi-K2.6"), samples: int = typer.Option(8), max_tokens: int = typer.Option(4096),
           limit: int = typer.Option(None), max_spend: float = typer.Option(6.0),
           estimate_only: bool = typer.Option(False, "--estimate"), yes: bool = typer.Option(False, "--yes")) -> None:
    renderer_name = LEADERBOARD_RENDERERS[model]
    tasks = train_tasks(limit)
    renderer, _ = make_renderer(model, renderer_name)
    # price only what will actually run: tasks whose samples are already recorded are skipped below
    done_tasks: set[str] = set()
    if RAW_TINKER_PATH.exists():
        counts: dict[str, int] = {}
        for line in RAW_TINKER_PATH.read_text().splitlines():
            r = json.loads(line)
            if r["model"] == model:
                counts[r["task_id"]] = counts.get(r["task_id"], 0) + 1
        done_tasks = {t for t, n in counts.items() if n >= samples}
    est = estimate([t for t in tasks if t.id not in done_tasks], renderer, samples, max_tokens, model)
    est["already_sampled_tasks"] = len(done_tasks)
    typer.echo(json.dumps({**est, "renderer": renderer_name, "temperature": TEMPERATURE}, indent=2))
    if estimate_only:
        return
    if not yes:
        raise typer.BadParameter("this spends money: run with --estimate first, then pass --yes")
    if est["worst_usd"] > max_spend:
        raise typer.BadParameter(f"worst case ${est['worst_usd']} exceeds --max-spend ${max_spend}")
    load_tinker_key()
    import tinker
    from tinker_cookbook.renderers import get_text_content

    done = set()
    if RAW_TINKER_PATH.exists():
        for line in RAW_TINKER_PATH.read_text().splitlines():
            r = json.loads(line)
            done.add((r["task_id"], r["index"], r["prompt_hash"], r["model"]))
    client = tinker.ServiceClient().create_sampling_client(base_model=model)
    stop = renderer.get_stop_sequences()
    p = price(model)
    futures = []
    for t in tasks:
        messages = build_messages(t)
        ph = prompt_hash(messages)
        todo = [INDEX_OFFSET + i for i in range(samples) if (t.id, INDEX_OFFSET + i, ph, model) not in done]
        if not todo:
            continue
        prompt = renderer.build_generation_prompt(messages)
        params = tinker.SamplingParams(max_tokens=max_tokens, temperature=TEMPERATURE, stop=stop, seed=todo[0])
        futures.append((t, ph, todo, prompt.length, client.sample(prompt, num_samples=len(todo), sampling_params=params)))
    typer.echo(f"{sum(len(f[2]) for f in futures)} samples to run")
    spent, graded, passed = 0.0, 0, 0
    with RAW_TINKER_PATH.open("a") as f:
        for t, ph, todo, prompt_len, fut in futures:
            for idx, seq in zip(todo, fut.result().sequences):
                message, termination = renderer.parse_response(seq.tokens)
                text = get_text_content(message)
                cost = (prompt_len * p["prefill"] + len(seq.tokens) * p["sample"]) / 1e6
                spent += cost
                result = run_completion(t, text)
                f.write(json.dumps({"task_id": t.id, "index": idx, "model": model, "renderer": renderer_name, "prompt_hash": ph,
                                    "temperature": TEMPERATURE, "finish_reason": "length" if len(seq.tokens) >= max_tokens else str(termination),
                                    "cost_usd": round(cost, 6), "passed": result.passed, "leak": result.leak, "completion": text,
                                    "run_date": dt.datetime.now(dt.timezone.utc).date().isoformat()}) + "\n")
                graded += 1
                passed += result.passed
    typer.echo(json.dumps({"graded": graded, "passed": passed, "pass_rate": round(passed / graded, 3) if graded else None, "spent_usd": round(spent, 4)}))


def _raw_rows() -> list[dict[str, Any]]:
    rows = []
    for path in (RAW_PATH, RAW_TINKER_PATH):
        if path.exists():
            rows += [json.loads(line) for line in path.read_text().splitlines()]
    return rows


@app.command()
def rebuild(max_keep: int = typer.Option(6)) -> None:
    """data/sft_v3.jsonl: reference + up to K distinct passing answers per train task, round-robin over sources."""
    split = splitmod.load()
    train_ids = sorted(split["train"])
    by_task: dict[str, dict[str, list[dict[str, Any]]]] = defaultdict(lambda: defaultdict(list))
    for r in _raw_rows():
        if r["task_id"] in train_ids and r["passed"]:
            by_task[r["task_id"]][r["model"]].append(r)
    rows, stats = [], {}
    for tid in train_ids:
        task = Task.load(next(TASKS_DIR.glob(f"{tid}-*")))
        messages = build_messages(task)
        seen = {normalise_sql(task.solution_sql)}
        rows.append({"task_id": tid, "source": "reference", "messages": messages + [{"role": "assistant", "content": _assistant(task.solution_sql)}]})
        queues = {m: sorted(rs, key=lambda r: r["index"]) for m, rs in by_task.get(tid, {}).items()}
        kept: Counter = Counter()
        while sum(kept.values()) < max_keep and any(queues.values()):
            for m in sorted(queues):
                if not queues[m] or sum(kept.values()) >= max_keep:
                    continue
                r = queues[m].pop(0)
                sql = extract_sql_block(r["completion"])
                key = normalise_sql(sql)
                if key in seen:
                    continue
                seen.add(key)
                rows.append({"task_id": tid, "source": m, "messages": messages + [{"role": "assistant", "content": _assistant(sql)}]})
                kept[m] += 1
        stats[tid] = dict(kept)
    SFT_V3_PATH.write_text("".join(json.dumps(r) + "\n" for r in rows))
    by_source = Counter(r["source"] for r in rows)
    out = {"examples": len(rows), "by_source": dict(by_source), "tasks_at_cap": sum(sum(v.values()) >= max_keep for v in stats.values()),
           "reference_only": [t for t, v in stats.items() if not v], "per_task": stats}
    (ROOT / "results" / "train" / "sft_v3_stats.json").write_text(json.dumps(out, indent=2) + "\n")
    typer.echo(json.dumps({k: v for k, v in out.items() if k != "per_task"}, indent=2))


@app.command("dev-set")
def dev_set(max_keep: int = typer.Option(6)) -> None:
    """Rebuild data/sft_dev.jsonl from dev references plus passing dev-task samples from every source."""
    from eval.metrics import _latest

    dev_ids = sorted(splitmod.load()["dev"])
    sources = {}
    for path in DEV_SOURCES:
        if path.exists():
            sources[path.stem] = _latest(json.loads(line) for line in path.read_text().splitlines())
    rows, kept = [], {}
    for tid in dev_ids:
        task = Task.load(next(TASKS_DIR.glob(f"{tid}-*")))
        messages = build_messages(task)
        seen = {normalise_sql(task.solution_sql)}
        rows.append({"task_id": tid, "source": "reference", "messages": messages + [{"role": "assistant", "content": _assistant(task.solution_sql)}]})
        kept[tid] = Counter()
        queues = {name: [r for (t, _, _), r in sorted(latest.items()) if t == tid and r["result"]["passed"]] for name, latest in sources.items()}
        while sum(kept[tid].values()) < max_keep and any(queues.values()):
            for name in sorted(queues):
                if not queues[name] or sum(kept[tid].values()) >= max_keep:
                    continue
                r = queues[name].pop(0)
                sql = extract_sql_block(r["completion"])
                key = normalise_sql(sql)
                if key in seen:
                    continue
                seen.add(key)
                rows.append({"task_id": tid, "source": name, "messages": messages + [{"role": "assistant", "content": _assistant(sql)}]})
                kept[tid][name] += 1
    DEV_PATH.write_text("".join(json.dumps(r) + "\n" for r in rows))
    typer.echo(json.dumps({"examples": len(rows), "per_task": {t: dict(c) for t, c in kept.items()}}))


if __name__ == "__main__":
    app()
