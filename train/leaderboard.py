"""Leaderboard rows sampled on Tinker: base models on all 103 tasks with the baseline protocol, reasoning off.

Records go to results/tinker_eval/<slug>@reasoning-off.jsonl in the baseline format. `summarize`
merges every complete 103-task file (OpenRouter baselines, Anthropic, Tinker) into results/leaderboard.json.
"""

from __future__ import annotations

import json
import warnings
from pathlib import Path
from typing import Any

import typer

warnings.filterwarnings("ignore", message=r'Field "model_')

from eval.metrics import load_records, load_task_meta, model_metrics  # noqa: E402
from eval.prompts import build_messages  # noqa: E402
from eval.run_baselines import BASELINES_DIR  # noqa: E402
from harness.db import ROOT  # noqa: E402
from harness.models import Task  # noqa: E402
from train import eval_tinker  # noqa: E402
from train.sft_tinker import load_tinker_key, make_renderer  # noqa: E402

LEADERBOARD_PATH = ROOT / "results" / "leaderboard.json"
# model -> reasoning-off renderer (cookbook names); the cheapest faithful protocol for a base-model row
MODELS = {
    "Qwen/Qwen3.5-9B": "qwen3_5_disable_thinking",
    "moonshotai/Kimi-K2.6": "kimi_k26_disable_thinking",
    "Qwen/Qwen3.8-27B": "qwen3_8_disable_thinking",
    "openai/gpt-oss-120b": "gpt_oss_medium_reasoning",  # no reasoning-off template; medium is its default
    "Qwen/Qwen3.5-397B-A17B": "qwen3_5_disable_thinking",
}

app = typer.Typer(add_completion=False)


@app.callback()
def _cli() -> None:
    """Subcommands below."""


def all_tasks() -> list[Task]:
    return [Task.load(p) for p in sorted(ROOT.glob("tasks/T*")) if (p / "task.yaml").exists()]


def label(model: str) -> str:
    return f"{model.split('/')[-1]}@reasoning-off"


def plan(models: list[str], k: int, max_tokens: int) -> dict[str, Any]:
    tasks = all_tasks()
    out, total_typ, total_worst = {}, 0.0, 0.0
    for m in models:
        renderer, _ = make_renderer(m, MODELS[m])
        prompt_tokens = {t.id: renderer.build_generation_prompt(build_messages(t)).length for t in tasks}
        est = eval_tinker.estimate(prompt_tokens, m, k, max_tokens)
        out[m] = {"renderer": MODELS[m], **{key: round(v, 3) if isinstance(v, float) else v for key, v in est.items()}}
        total_typ += est["typical_usd"]
        total_worst += est["worst_usd"]
    return {"tasks": len(tasks), "k": k, "max_tokens": max_tokens, "models": out,
            "total_typical_usd": round(total_typ, 2), "total_worst_usd": round(total_worst, 2)}


@app.command()
def estimate(models: str = typer.Option(",".join(MODELS)), k: int = typer.Option(5), max_tokens: int = typer.Option(4096)) -> None:
    typer.echo(json.dumps(plan(models.split(","), k, max_tokens), indent=2))


@app.command()
def run(models: str = typer.Option(",".join(MODELS)), k: int = typer.Option(5), max_tokens: int = typer.Option(4096),
        max_spend_per_model: float = typer.Option(5.0), yes: bool = typer.Option(False, "--yes")) -> None:
    names = models.split(",")
    p = plan(names, k, max_tokens)
    typer.echo(json.dumps(p, indent=2))
    if not yes:
        raise typer.BadParameter("this spends money: run `estimate` first, then pass --yes")
    load_tinker_key()
    import tinker

    service = tinker.ServiceClient()
    tasks = all_tasks()
    for m in names:
        renderer, _ = make_renderer(m, MODELS[m])
        client = service.create_sampling_client(base_model=m)
        out = eval_tinker.sample_and_grade(client, renderer, tasks, label=label(m), model=m, model_path=None,
                                           renderer_name=MODELS[m], k=k, max_tokens=max_tokens,
                                           max_spend=max_spend_per_model, log=lambda s: None)
        typer.echo(json.dumps({"model": m, **{key: round(v, 4) if isinstance(v, float) else v for key, v in out.items()}}))
    summarize()


@app.command()
def summarize() -> None:
    """Merge every complete 103-task result file into results/leaderboard.json."""
    metas = load_task_meta()
    rows: dict[str, Any] = {}
    for path in sorted(BASELINES_DIR.glob("*.jsonl")) + sorted((ROOT / "results" / "tinker_eval").glob("*@reasoning-off.jsonl")):
        records = load_records(path)
        if not records:
            continue
        m = model_metrics(records, metas)
        if not m["complete"]:
            continue
        rows[path.stem] = {"provider": records[0].get("provider") if "provider" in records[0] else "openrouter",
                           "reasoning": m["reasoning"], "max_tokens": m["max_tokens"], "pass_at_1": m["pass_at_1"],
                           "pass_at_5": m["pass_at_5"], "leak_rate": m["leak_rate"], "block_rate": m["block_rate"],
                           "apply_error_rate": m["apply_error_rate"], "format_error_rate": m["format_error_rate"],
                           "truncation_rate": m["truncation_rate"], "by_tier": m["by_tier"], "by_trap": m["by_trap"],
                           "run_dates": m["run_dates"], "spend_usd": m["spend_usd"], "source": str(path.relative_to(ROOT))}
    LEADERBOARD_PATH.write_text(json.dumps({"tasks": len(metas), "models": rows}, indent=2) + "\n")
    for name, r in sorted(rows.items(), key=lambda kv: -kv[1]["pass_at_1"]["rate"]):
        typer.echo(f"{name:55} pass@1 {r['pass_at_1']['rate']:.0%}  pass@5 {r['pass_at_5']['rate'] or 0:.0%}  leak {r['leak_rate']['rate']:.0%}")


if __name__ == "__main__":
    app()
