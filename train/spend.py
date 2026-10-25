"""Total estimated Tinker spend from the stored records, at the list prices in the scripts (no API calls).

Writes results/train/tinker_spend.json. Every figure is an estimate from token counts, not an invoice.
"""

from __future__ import annotations

import json
from pathlib import Path

import typer

from eval.prompts import build_messages
from harness.db import ROOT
from train import eval_tinker
from train.build_sft import train_tasks
from train.prices import PRICES
from train.sft_tinker import CHECKPOINTS_PATH, RESULTS_DIR, make_renderer


def _conversation_tokens(path: Path, model: str, renderer_name: str) -> int:
    from tinker_cookbook import renderers
    from tinker_cookbook.supervised.data import conversation_to_datum

    renderer, _ = make_renderer(model, renderer_name)
    rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    return sum(conversation_to_datum(r["messages"], renderer, None, renderers.TrainOnWhat.LAST_ASSISTANT_MESSAGE).model_input.length for r in rows)

app = typer.Typer(add_completion=False)


def _eval_cost(paths: list[Path]) -> float:
    """Sum of per-sample costs; 3-try (repair) files carry their cost in the matching .summary.json instead."""
    total = 0.0
    for p in paths:
        if p.name.endswith("@repair3.jsonl"):
            summary = p.with_name(p.name.replace(".jsonl", ".summary.json"))
            total += json.loads(summary.read_text()).get("est_spend_usd", 0.0) if summary.exists() else 0.0
            continue
        total += sum(r.get("cost_usd", 0.0) for r in map(json.loads, p.read_text().splitlines()))
    return total


@app.command()
def main() -> None:
    checkpoints = json.loads(CHECKPOINTS_PATH.read_text())
    items: dict[str, float] = {}
    for r in checkpoints:
        label = f"{r['kind']} run {r.get('name', r['run_id'])} ({r['steps']} steps)"
        if "est_spend_usd" in r:  # RL runs include their in-loop dev evals
            items[label] = r["est_spend_usd"]
        else:  # cookbook SFT runs: trained tokens from the metrics, dev-loss prefill from the dev file
            metrics = [json.loads(line) for line in (ROOT / r["metrics"]).read_text().splitlines()]
            p = PRICES[r["model"]]
            train_tokens = sum(m.get("num_tokens", 0) for m in metrics)
            n_evals = sum("test/nll" in m for m in metrics)
            dev_path = ROOT / "data" / ("judge_dev.jsonl" if r.get("recipe") == "rls_bench_judge" else "sft_dev.jsonl")
            dev_tokens = _conversation_tokens(dev_path, r["model"], r["renderer"]) if dev_path.exists() else 0
            items[label] = (train_tokens * p["train"] + n_evals * dev_tokens * p["prefill"]) / 1e6
    for p in sorted(RESULTS_DIR.glob("rl_filter_*.jsonl")):
        rows = [json.loads(line) for line in p.read_text().splitlines()]
        ck = eval_tinker.checkpoint(p.stem.removeprefix("rl_filter_"))
        renderer, _ = make_renderer(ck["model"], ck["renderer"])
        prompt = {t.id: renderer.build_generation_prompt(build_messages(t)).length for t in train_tasks()}
        price = eval_tinker.SAMPLE_PRICES[ck["model"]]
        items[f"GRPO filter pass {p.stem}"] = sum(prompt[r["task_id"]] * price["prefill"]
                                                  + r["completion_tokens"] * price["sample"] for r in rows) / 1e6
    # Standalone evals on Tinker: dev evals of checkpoints, leaderboard rows; in-loop RL dev evals are in the run totals.
    for p in sorted(eval_tinker.EVAL_DIR.glob("*.jsonl")):
        if "@rl" in p.name or "-eval0" in p.name or "@repair" in p.name:
            continue
        kind = "leaderboard row" if "@reasoning-off" in p.name else "dev eval"
        items[f"{kind} {p.stem}"] = _eval_cost([p])
    for name, d in (("one-time test eval v1 (3 models)", ROOT / "results" / "test_eval"), ("test eval v2", ROOT / "results" / "test_eval_v2")):
        if d.exists():
            items[name] = _eval_cost(sorted(d.glob("*.jsonl")))
    for p in sorted((ROOT / "results" / "judge").glob("*.cost.json")):
        if "opus" not in p.name:  # Opus judgements are on the Anthropic credit, not Tinker
            items[f"judge {p.name.replace('.cost.json', '')}"] = json.loads(p.read_text())["est_spend_usd"]
    out = {"note": "estimates at list prices from token counts", "items": {k: round(v, 4) for k, v in items.items()},
           "total_usd": round(sum(items.values()), 4)}
    path = RESULTS_DIR / "tinker_spend.json"
    path.write_text(json.dumps(out, indent=2) + "\n")
    typer.echo(path.read_text())


if __name__ == "__main__":
    app()
