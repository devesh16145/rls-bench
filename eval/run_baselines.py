"""Sample a model on tasks through OpenRouter, grade every sample, append raw lines to results/baselines/."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
from concurrent.futures import FIRST_COMPLETED, Future, ThreadPoolExecutor, wait
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

import httpx

from eval import openrouter
from eval.prompts import build_messages, prompt_hash
from harness.db import ROOT
from harness.models import Task
from harness.runner import run_completion

BASELINES_DIR = ROOT / "results" / "baselines"
GREEDY_TEMPERATURE = 0.0
SAMPLE_TEMPERATURE = 0.7
CHARS_PER_TOKEN = 4  # rough; used only for estimates, never for reported numbers
TYPICAL_OUTPUT_TOKENS = 3000
TYPICAL_OUTPUT_TOKENS_NO_REASONING = 1500
# provider default vs. reasoning disabled; stored with every sample and kept in separate result files
REASONING_SETTINGS: dict[str, dict[str, Any] | None] = {"default": None, "off": {"enabled": False}}


@dataclass(frozen=True)
class Sample:
    task: Task
    temperature: float
    index: int


def model_slug(model: str) -> str:
    return model.replace("/", "__").replace(":", "_")


def results_path(model: str, reasoning: str = "default") -> Path:
    suffix = "" if reasoning == "default" else f"@reasoning-{reasoning}"
    return BASELINES_DIR / f"{model_slug(model)}{suffix}.jsonl"


def reasoning_tokens(usage: dict[str, Any]) -> int:
    return int((usage.get("completion_tokens_details") or {}).get("reasoning_tokens") or 0)


def plan_samples(tasks: list[Task], k: int) -> list[Sample]:
    samples = []
    for t in tasks:
        samples.append(Sample(t, GREEDY_TEMPERATURE, 0))
        samples.extend(Sample(t, SAMPLE_TEMPERATURE, i) for i in range(k))
    return samples


def tests_hash(task: Task) -> str:
    """Fingerprint of the tests a sample was graded against."""
    from harness.runner import HARNESS_VERSION

    data = (task.path / "tests.yaml").read_bytes() + b"\0harness=" + HARNESS_VERSION.encode()
    return hashlib.sha256(data).hexdigest()[:16]


def regrade(path: Path, tasks: list[Task], log: Callable[[str], None] = print) -> dict[str, int]:
    """Re-grade stored completions against the current tests. Appends new records; never rewrites old ones."""
    by_id = {t.id: t for t in tasks}
    latest: dict[tuple[str, float, int], dict[str, Any]] = {}
    for line in path.read_text().splitlines():
        r = json.loads(line)
        latest[(r["task_id"], r["temperature"], r["index"])] = r
    regraded = changed = 0
    today = dt.datetime.now(dt.timezone.utc).date().isoformat()
    with path.open("a") as f:
        for key, r in sorted(latest.items()):
            task = by_id.get(r["task_id"])
            if task is None or r.get("tests_hash") == tests_hash(task):
                continue
            result = run_completion(task, r["completion"])
            changed += result.passed != r["result"]["passed"]
            new = {**r, "result": result.model_dump(), "tests_hash": tests_hash(task),
                   "regraded_on": today, "cost_usd": 0.0}
            f.write(json.dumps(new) + "\n")
            regraded += 1
    log(f"{path.name}: regraded {regraded} samples, {changed} changed pass/fail")
    return {"regraded": regraded, "changed": changed}


def _done_keys(path: Path) -> set[tuple[str, float, int, str, int]]:
    if not path.exists():
        return set()
    keys = set()
    for line in path.read_text().splitlines():
        r = json.loads(line)
        keys.add((r["task_id"], r["temperature"], r["index"], r["prompt_hash"], r["max_tokens"]))
    return keys


def estimate(model: str, tasks: list[Task], k: int, max_tokens: int, reasoning: str = "default") -> dict[str, Any]:
    """Cost estimate from live OpenRouter prices. Input tokens approximated as chars / 4."""
    info = openrouter.model_info(model)
    pricing = info.get("pricing", {})
    price_in = float(pricing.get("prompt") or 0)
    price_out = float(pricing.get("completion") or 0)
    samples = plan_samples(tasks, k)
    input_tokens = 0
    prompt_chars: dict[str, int] = {}
    for s in samples:
        if s.task.id not in prompt_chars:
            prompt_chars[s.task.id] = sum(len(m["content"]) for m in build_messages(s.task))
        input_tokens += prompt_chars[s.task.id] // CHARS_PER_TOKEN
    typical = TYPICAL_OUTPUT_TOKENS if reasoning == "default" else TYPICAL_OUTPUT_TOKENS_NO_REASONING
    typical_out = len(samples) * min(typical, max_tokens)
    worst_out = len(samples) * max_tokens
    params = info.get("supported_parameters") or []
    return {
        "model": model,
        "samples": len(samples),
        "tasks": len(tasks),
        "price_in_per_m": price_in * 1e6,
        "price_out_per_m": price_out * 1e6,
        "input_tokens": input_tokens,
        "typical_output_tokens": typical_out,
        "worst_output_tokens": worst_out,
        "typical_usd": input_tokens * price_in + typical_out * price_out,
        "worst_usd": input_tokens * price_in + worst_out * price_out,
        "honours_temperature": "temperature" in params,
        "reasoning": reasoning,
        "reasoning_optional": not ((info.get("reasoning") or {}).get("mandatory", False)),
    }


def run_model(
    model: str,
    tasks: list[Task],
    *,
    k: int,
    max_tokens: int,
    max_spend: float,
    concurrency: int = 4,
    reasoning: str = "default",
    log: Callable[[str], None] = print,
) -> dict[str, Any]:
    """Sample, grade and append. Stops submitting new requests once spend reaches max_spend.

    With reasoning="off", stops as soon as a fresh sample reports reasoning tokens (setting ignored).
    """
    reasoning_param = REASONING_SETTINGS[reasoning]
    info = openrouter.model_info(model)
    send_temperature = "temperature" in (info.get("supported_parameters") or [])
    out_path = results_path(model, reasoning)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    done = _done_keys(out_path)

    jobs = []
    for s in plan_samples(tasks, k):
        messages = build_messages(s.task)
        ph = prompt_hash(messages)
        if (s.task.id, s.temperature, s.index, ph, max_tokens) not in done:
            jobs.append((s, messages, ph))
    log(f"{model}: {len(jobs)} samples to run ({len(done)} already recorded); temperature sent: {send_temperature}")

    spent = 0.0
    graded = 0
    stopped = False
    stop_reason: str | None = None
    run_date = dt.datetime.now(dt.timezone.utc).date().isoformat()
    with httpx.Client(timeout=600) as client, ThreadPoolExecutor(max_workers=concurrency) as pool:
        pending: dict[Future, tuple[Sample, str]] = {}
        queue = list(jobs)

        def submit_next() -> None:
            s, messages, ph = queue.pop(0)
            fut = pool.submit(
                openrouter.complete,
                model,
                messages,
                prompt_hash=ph,
                temperature=s.temperature,
                index=s.index,
                max_tokens=max_tokens,
                send_temperature=send_temperature,
                reasoning=reasoning_param,
                client=client,
            )
            pending[fut] = (s, ph)

        while queue and len(pending) < concurrency:
            submit_next()
        while pending:
            finished, _ = wait(pending, return_when=FIRST_COMPLETED)
            for fut in finished:
                s, ph = pending.pop(fut)
                completion = fut.result()
                if not completion.cached:
                    spent += completion.cost_usd
                result = run_completion(s.task, completion.text)
                record = {
                    "model": model,
                    "task_id": s.task.id,
                    "temperature": s.temperature,
                    "temperature_sent": send_temperature,
                    "reasoning": reasoning,
                    "reasoning_tokens": reasoning_tokens(completion.usage),
                    "index": s.index,
                    "max_tokens": max_tokens,
                    "prompt_hash": ph,
                    "tests_hash": tests_hash(s.task),
                    "run_date": run_date,
                    "provider": completion.provider,
                    "finish_reason": completion.finish_reason,
                    "usage": completion.usage,
                    "cost_usd": completion.cost_usd,
                    "completion": completion.text,
                    "result": result.model_dump(),
                }
                with out_path.open("a") as f:
                    f.write(json.dumps(record) + "\n")
                graded += 1
                status = "PASS" if result.passed else ("LEAK" if result.leak else "FAIL")
                log(f"  [{graded}/{len(jobs)}] {s.task.id} t={s.temperature} #{s.index} {status}  spend ${spent:.2f}")
                if reasoning == "off" and not completion.cached and reasoning_tokens(completion.usage) > 0 and not stopped:
                    stopped = True
                    stop_reason = "reasoning-not-disabled"
                    log(f"reasoning was not disabled ({reasoning_tokens(completion.usage)} reasoning tokens); stopping")
                    queue.clear()
            if spent >= max_spend and queue and not stopped:
                stopped = True
                stop_reason = "spend-cap"
                log(f"spend cap ${max_spend:.2f} reached; not submitting {len(queue)} remaining samples")
                queue.clear()
            while queue and len(pending) < concurrency:
                submit_next()

    return {"model": model, "graded": graded, "spent_usd": spent, "stopped_at_cap": stop_reason == "spend-cap", "stopped": stopped, "stop_reason": stop_reason, "path": str(out_path)}
