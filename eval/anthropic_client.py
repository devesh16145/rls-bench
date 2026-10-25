"""Baseline samples from Claude through the Anthropic API (spec §7), in the OpenRouter record format.

Same protocol as eval/run_baselines.py: one greedy-slot sample (index 0, recorded temperature 0) plus k
samples per task. The API does not accept a temperature, so `temperature_sent` is false and the model's
default sampling applies to every sample; thinking is always on for Opus 5.5 and its depth is the
`effort` setting, recorded with every sample. Responses are cached on disk like OpenRouter's.

Run: `python -m eval.anthropic_client estimate|run`.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import warnings
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import typer

warnings.filterwarnings("ignore", message=r'Field "model_')

from eval.prompts import build_messages, prompt_hash  # noqa: E402
from eval.run_baselines import BASELINES_DIR, CHARS_PER_TOKEN, _done_keys, plan_samples, tests_hash  # noqa: E402
from harness.db import ROOT  # noqa: E402
from harness.models import Task  # noqa: E402
from harness.runner import run_completion  # noqa: E402
from train.prices import ANTHROPIC_PRICES  # noqa: E402

CACHE_DIR = ROOT / ".rlsbench" / "cache" / "anthropic"
DEFAULT_MODEL = "claude-opus-5-5"
DEFAULT_EFFORT = "medium"  # the model's own default; recorded with every sample
TYPICAL_OUTPUT_TOKENS = 3000  # thinking included; estimate only

app = typer.Typer(add_completion=False)


@app.callback()
def _cli() -> None:
    """Subcommands below."""


@dataclass
class Completion:
    text: str
    usage: dict[str, Any]
    cost_usd: float
    finish_reason: str | None
    cached: bool


def load_api_key() -> None:
    if os.environ.get("ANTHROPIC_API_KEY"):
        return
    env_file = ROOT / ".env"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            name, sep, value = line.partition("=")
            if sep and name.strip() == "ANTHROPIC_API_KEY":
                os.environ["ANTHROPIC_API_KEY"] = value.strip().strip('"').strip("'")
                return
    raise RuntimeError("ANTHROPIC_API_KEY is not set (add it to .env)")


def cost_usd(model: str, usage: dict[str, Any]) -> float:
    p = ANTHROPIC_PRICES[model]
    return (usage.get("input_tokens", 0) * p["input"] + usage.get("output_tokens", 0) * p["output"]) / 1e6


def complete(client, model: str, messages: list[dict[str, str]], *, prompt_hash: str, index: int, max_tokens: int,
             effort: str) -> Completion:
    key = json.dumps({"model": model, "prompt_hash": prompt_hash, "index": index, "max_tokens": max_tokens, "effort": effort}, sort_keys=True)
    path = CACHE_DIR / (hashlib.sha256(key.encode()).hexdigest()[:24] + ".json")
    if path.exists():
        data = json.loads(path.read_text())
        return Completion(**{**data, "cached": True})
    system = "\n\n".join(m["content"] for m in messages if m["role"] == "system")
    user = [{"role": m["role"], "content": m["content"]} for m in messages if m["role"] != "system"]
    with client.messages.stream(model=model, max_tokens=max_tokens, system=system, messages=user,
                                output_config={"effort": effort}) as stream:
        msg = stream.get_final_message()
    text = "".join(block.text for block in msg.content if block.type == "text")
    usage = {"input_tokens": msg.usage.input_tokens, "output_tokens": msg.usage.output_tokens,
             "cache_read_input_tokens": getattr(msg.usage, "cache_read_input_tokens", None) or 0}
    finish = {"end_turn": "stop", "max_tokens": "length", "stop_sequence": "stop"}.get(msg.stop_reason, msg.stop_reason)
    data = {"text": text, "usage": usage, "cost_usd": cost_usd(model, usage), "finish_reason": finish}
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data))
    return Completion(**data, cached=False)


def results_path(model: str, effort: str) -> Path:
    return BASELINES_DIR / f"{model}@effort-{effort}.jsonl"


def _tasks(task_ids: list[str] | None) -> list[Task]:
    dirs = sorted(p for p in (ROOT / "tasks").glob("T*") if (p / "task.yaml").exists())
    tasks = [Task.load(p) for p in dirs]
    if task_ids:
        tasks = [t for t in tasks if t.id in task_ids]
    return tasks


def estimate_cost(tasks: list[Task], k: int, max_tokens: int, model: str) -> dict[str, Any]:
    p = ANTHROPIC_PRICES[model]
    samples = plan_samples(tasks, k)
    input_tokens = sum(sum(len(m["content"]) for m in build_messages(s.task)) // CHARS_PER_TOKEN for s in samples)
    return {"model": model, "tasks": len(tasks), "samples": len(samples), "input_tokens": input_tokens,
            "typical_usd": round((input_tokens * p["input"] + len(samples) * min(TYPICAL_OUTPUT_TOKENS, max_tokens) * p["output"]) / 1e6, 2),
            "worst_usd": round((input_tokens * p["input"] + len(samples) * max_tokens * p["output"]) / 1e6, 2)}


@app.command()
def estimate(model: str = typer.Option(DEFAULT_MODEL), k: int = typer.Option(5), max_tokens: int = typer.Option(16000),
             task: list[str] = typer.Option(None, "--task")) -> None:
    typer.echo(json.dumps(estimate_cost(_tasks(task), k, max_tokens, model), indent=2))


@app.command()
def run(
    model: str = typer.Option(DEFAULT_MODEL),
    k: int = typer.Option(5),
    max_tokens: int = typer.Option(16000),
    effort: str = typer.Option(DEFAULT_EFFORT),
    task: list[str] = typer.Option(None, "--task"),
    max_spend: float = typer.Option(20.0),
    concurrency: int = typer.Option(4),
    yes: bool = typer.Option(False, "--yes"),
) -> None:
    tasks = _tasks(task)
    est = estimate_cost(tasks, k, max_tokens, model)
    typer.echo(json.dumps({**est, "effort": effort}, indent=2))
    if not yes:
        raise typer.BadParameter("this spends money: check the estimate, then pass --yes")
    load_api_key()
    import anthropic

    client = anthropic.Anthropic(max_retries=4)
    out_path = results_path(model, effort)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    done = _done_keys(out_path)
    jobs = []
    for s in plan_samples(tasks, k):
        messages = build_messages(s.task)
        ph = prompt_hash(messages)
        if (s.task.id, s.temperature, s.index, ph, max_tokens) not in done:
            jobs.append((s, messages, ph))
    typer.echo(f"{model}: {len(jobs)} samples to run ({len(done)} already recorded)")
    run_date = dt.datetime.now(dt.timezone.utc).date().isoformat()
    spent, graded, stopped = 0.0, 0, False
    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        futures, queue = {}, list(jobs)

        def submit() -> None:
            s, messages, ph = queue.pop(0)
            # the greedy slot and the k sampled slots share the cache key space by index: slot 0 is index 1000
            idx = 1000 if s.temperature == 0.0 else s.index
            futures[pool.submit(complete, client, model, messages, prompt_hash=ph, index=idx, max_tokens=max_tokens, effort=effort)] = (s, ph)

        while queue and len(futures) < concurrency:
            submit()
        while futures:
            fut = next(as_completed(futures))
            s, ph = futures.pop(fut)
            try:
                c = fut.result()
            except anthropic.APIError as exc:
                if not stopped:
                    stopped = True
                    typer.echo(f"stopping: {type(exc).__name__}: {str(exc)[:200]}; {len(queue)} samples not submitted")
                    queue.clear()
                continue
            if not c.cached:
                spent += c.cost_usd
            result = run_completion(s.task, c.text)
            record = {
                "model": model, "task_id": s.task.id, "temperature": s.temperature, "temperature_sent": False,
                "reasoning": f"effort-{effort}", "reasoning_tokens": None, "index": s.index, "max_tokens": max_tokens,
                "prompt_hash": ph, "tests_hash": tests_hash(s.task), "run_date": run_date, "provider": "anthropic",
                "finish_reason": c.finish_reason, "usage": c.usage, "cost_usd": c.cost_usd, "completion": c.text,
                "result": result.model_dump(),
            }
            with out_path.open("a") as f:
                f.write(json.dumps(record) + "\n")
            graded += 1
            status = "PASS" if result.passed else ("LEAK" if result.leak else "FAIL")
            if graded % 10 == 0 or not queue:
                typer.echo(f"  [{graded}/{len(jobs)}] {s.task.id} #{s.index} {status}  spend ${spent:.2f}")
            if spent >= max_spend and queue and not stopped:
                stopped = True
                typer.echo(f"spend cap ${max_spend:.2f} reached; {len(queue)} samples not submitted")
                queue.clear()
            while queue and len(futures) < concurrency:
                submit()
    typer.echo(json.dumps({"graded": graded, "spent_usd": round(spent, 4), "stopped": stopped, "path": str(out_path.relative_to(ROOT))}))


if __name__ == "__main__":
    app()
