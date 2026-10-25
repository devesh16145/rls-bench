"""Aggregate raw baseline lines into metrics with 95% Wilson intervals (spec §7.3)."""

from __future__ import annotations

import datetime as dt
import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

from harness.db import ROOT
from harness.models import TaskMeta

import yaml

TASKS_DIR = ROOT / "tasks"
Z95 = 1.959963984540054


def wilson(successes: int, n: int) -> dict[str, float | int]:
    if n == 0:
        return {"rate": 0.0, "lo": 0.0, "hi": 0.0, "n": 0}
    p = successes / n
    denom = 1 + Z95**2 / n
    centre = (p + Z95**2 / (2 * n)) / denom
    half = Z95 * math.sqrt(p * (1 - p) / n + Z95**2 / (4 * n * n)) / denom
    return {"rate": p, "lo": max(0.0, centre - half), "hi": min(1.0, centre + half), "n": n}


def pass_at_k(n: int, c: int, k: int) -> float:
    """Unbiased estimator 1 - C(n-c, k) / C(n, k). With n == k this is 'any of k passed'."""
    if n < k:
        raise ValueError(f"need at least k={k} samples, got {n}")
    if n - c < k:
        return 1.0
    return 1.0 - math.comb(n - c, k) / math.comb(n, k)


def cohen_kappa(a: list[bool], b: list[bool]) -> float:
    if len(a) != len(b) or not a:
        raise ValueError("need two equal-length, non-empty label lists")
    n = len(a)
    observed = sum(x == y for x, y in zip(a, b)) / n
    pa, pb = sum(a) / n, sum(b) / n
    expected = pa * pb + (1 - pa) * (1 - pb)
    return 1.0 if expected == 1 else (observed - expected) / (1 - expected)


def load_split_map() -> dict[str, str]:
    """task id -> 'train' | 'dev' | 'test', from the frozen split (empty before it exists)."""
    path = TASKS_DIR / "split.json"
    if not path.exists():
        return {}
    split = json.loads(path.read_text())
    return {tid: name for name in ("train", "dev", "test") for tid in split[name]}


def load_task_meta() -> dict[str, TaskMeta]:
    metas = {}
    for p in sorted(TASKS_DIR.glob("T*/task.yaml")):
        m = TaskMeta.model_validate(yaml.safe_load(p.read_text()))
        metas[m.id] = m
    return metas


def load_records(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def _latest(records: Iterable[dict[str, Any]]) -> dict[tuple[str, float, int], dict[str, Any]]:
    """One record per (task, temperature, index): the last one written wins."""
    out: dict[tuple[str, float, int], dict[str, Any]] = {}
    for r in records:
        out[(r["task_id"], r["temperature"], r["index"])] = r
    return out


def _pass_at_5(groups: list[list[bool]], k: int) -> dict[str, Any]:
    vals = [pass_at_k(len(v), sum(v), k) for v in groups if len(v) >= k]
    return {"rate": sum(vals) / len(vals) if vals else None, "n": len(vals)}


def _rates(results: list[dict[str, Any]]) -> dict[str, Any]:
    n = len(results)
    return {
        "pass": wilson(sum(r["passed"] for r in results), n),
        "leak": wilson(sum(r["leak"] for r in results), n),
        "block": wilson(sum(r["block"] for r in results), n),
        "apply_error": wilson(sum(bool(r["apply_error"]) for r in results), n),
        "format_error": wilson(sum(bool(r["format_error"]) for r in results), n),
    }


def model_metrics(records: list[dict[str, Any]], metas: dict[str, TaskMeta], k: int = 5) -> dict[str, Any]:
    latest = _latest(records)
    greedy = {tid: r["result"] for (tid, temp, idx), r in latest.items() if temp == 0.0 and idx == 0 and tid in metas}
    greedy_records = [r for (tid, temp, idx), r in latest.items() if temp == 0.0 and idx == 0 and tid in metas]
    all_records = [r for (tid, _, _), r in latest.items() if tid in metas]
    sampled: dict[str, list[bool]] = defaultdict(list)
    for (tid, temp, _), r in latest.items():
        if temp != 0.0 and tid in metas:
            sampled[tid].append(r["result"]["passed"])

    overall = _rates(list(greedy.values()))
    pass5 = [pass_at_k(len(v), sum(v), k) for v in sampled.values() if len(v) >= k]
    overall["pass_at_5"] = {"rate": sum(pass5) / len(pass5) if pass5 else None, "n": len(pass5)}

    split_of = load_split_map()
    groups: dict[str, dict[str, list[dict[str, Any]]]] = {
        "tier": defaultdict(list), "tag": defaultdict(list), "trap": defaultdict(list), "split": defaultdict(list),
    }
    for tid, res in greedy.items():
        m = metas[tid]
        groups["tier"][str(m.tier)].append(res)
        if tid in split_of:
            groups["split"][split_of[tid]].append(res)
        for tag in m.tags:
            groups["tag"][tag].append(res)
        for trap in m.traps:
            groups["trap"][trap].append(res)

    first = records[0] if records else {}
    return {
        "model": first.get("model"),
        "run_dates": sorted({r["run_date"] for r in records}),
        "temperature_sent": sorted({r["temperature_sent"] for r in records}),
        "max_tokens": sorted({r["max_tokens"] for r in records}),
        "reasoning": sorted({r.get("reasoning", "default") for r in records}),
        "prompt_hashes": len({r["prompt_hash"] for r in records}),
        "samples": len(latest),
        "tasks_covered": len(greedy),
        "complete": len(greedy) == len(metas),
        "records": len(records),
        "spend_usd": round(sum(r.get("cost_usd") or 0 for r in records), 4),
        "tests_hashes": len({r.get("tests_hash") for (_, _, _), r in latest.items()}),
        "pass_at_1": overall["pass"],
        "pass_at_5": overall["pass_at_5"],
        "leak_rate": overall["leak"],
        "block_rate": overall["block"],
        "apply_error_rate": overall["apply_error"],
        "format_error_rate": overall["format_error"],
        # answer cut off by max_tokens (reasoning counts against the cap); a subset of format errors
        "truncation_rate": wilson(sum(r.get("finish_reason") == "length" for r in greedy_records), len(greedy_records)),
        "truncation_rate_all_samples": wilson(sum(r.get("finish_reason") == "length" for r in all_records), len(all_records)),
        "by_tier": {key: _rates(v) for key, v in sorted(groups["tier"].items())},
        "by_tag": {key: _rates(v) for key, v in sorted(groups["tag"].items())},
        "by_trap": {key: _rates(v) for key, v in sorted(groups["trap"].items())},
        "by_split": {
            key: {
                **_rates(v),
                "pass_at_5": _pass_at_5([vals for tid, vals in sampled.items() if split_of.get(tid) == key], k),
            }
            for key, v in sorted(groups["split"].items())
        },
        "per_task": {
            tid: {"passed": r["passed"], "leak": r["leak"], "block": r["block"],
                  "apply_error": r["apply_error"], "format_error": r["format_error"]}
            for tid, r in sorted(greedy.items())
        },
    }


def summarize(baselines_dir: Path, out_path: Path) -> dict[str, Any]:
    metas = load_task_meta()
    models = {}
    for path in sorted(baselines_dir.glob("*.jsonl")):
        records = load_records(path)
        if records:
            models[path.stem] = model_metrics(records, metas)
    summary = {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "tasks": {
            tid: {"tier": m.tier, "tags": m.tags, "traps": m.traps, "verified": m.verified, "title": m.title}
            for tid, m in metas.items()
        },
        "models": models,
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(summary, indent=2) + "\n")
    return summary
