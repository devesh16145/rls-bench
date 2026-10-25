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
from train.sft_tinker import CHECKPOINTS_PATH, RESULTS_DIR, make_renderer

app = typer.Typer(add_completion=False)


def _eval_cost(paths: list[Path]) -> float:
    return sum(r["cost_usd"] for p in paths for r in map(json.loads, p.read_text().splitlines()))


@app.command()
def main() -> None:
    checkpoints = json.loads(CHECKPOINTS_PATH.read_text())
    items: dict[str, float] = {}
    for r in checkpoints:
        # RL runs already include their in-loop dev evals.
        items[f"{r['kind']} run {r['run_id']} ({r['steps']} steps)"] = r["est_spend_usd"]
    for p in sorted(RESULTS_DIR.glob("rl_filter_*.jsonl")):
        rows = [json.loads(line) for line in p.read_text().splitlines()]
        ck = eval_tinker.checkpoint(p.stem.removeprefix("rl_filter_"))
        renderer, _ = make_renderer(ck["model"], ck["renderer"])
        prompt = {t.id: renderer.build_generation_prompt(build_messages(t)).length for t in train_tasks()}
        price = eval_tinker.SAMPLE_PRICES[ck["model"]]
        items[f"GRPO filter pass {p.stem}"] = sum(prompt[r["task_id"]] * price["prefill"]
                                                  + r["completion_tokens"] * price["sample"] for r in rows) / 1e6
    standalone = [p for p in sorted(eval_tinker.EVAL_DIR.glob("*.jsonl")) if "@rl-" not in p.name]
    for p in standalone:
        items[f"dev eval {p.stem}"] = _eval_cost([p])
    test_dir = ROOT / "results" / "test_eval"
    items["one-time test eval (3 models)"] = _eval_cost(sorted(test_dir.glob("*.jsonl")))
    out = {"note": "estimates at list prices from token counts", "items": {k: round(v, 4) for k, v in items.items()},
           "total_usd": round(sum(items.values()), 4)}
    path = RESULTS_DIR / "tinker_spend.json"
    path.write_text(json.dumps(out, indent=2) + "\n")
    typer.echo(path.read_text())


if __name__ == "__main__":
    app()
