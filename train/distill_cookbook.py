"""Experiment C: on-policy distillation on the cookbook's recipe, with the harness environment as prompts only.

The student samples its own answers to train-task prompts; a teacher that shares its tokenizer scores every
student token; the student is trained to lower the per-token KL to the teacher. The environment's reward is
scaled to zero, so this is pure distillation (no correctness signal), which makes it a clean comparison
with SFT and GRPO at matched rollouts. Dev is evaluated with the baseline protocol every `eval_every` steps.

`--dry-run` prints the plan and estimate; no Tinker call.
"""

from __future__ import annotations

import asyncio
import datetime as dt
import json
import warnings

import typer

warnings.filterwarnings("ignore", message=r'Field "model_')

from harness.db import ROOT  # noqa: E402
from train import eval_tinker, rl_env  # noqa: E402
from train.build_sft import train_tasks  # noqa: E402
from train.prices import price, rollout_usd  # noqa: E402
from train.rl_cookbook import DEFAULT_MODEL, DEFAULT_RENDERERS, TYPICAL_COMPLETION_TOKENS, checkpoint_record  # noqa: E402
from train.sft_tinker import CHECKPOINTS_PATH, RESULTS_DIR, load_tinker_key  # noqa: E402

DEFAULT_TEACHER = "Qwen/Qwen3.5-397B-A17B"  # same tokenizer family as the student; sampleable on Tinker

app = typer.Typer(add_completion=False)


@app.callback()
def _cli() -> None:
    """Subcommands below."""


def estimate(prompt_tokens: dict[str, int], batches, group_size: int, max_tokens: int, model: str, teacher: str) -> dict:
    """Student rollout + training cost, plus the teacher scoring every full sequence at its prefill price."""
    tp = price(teacher)["prefill"]
    typ = worst = 0.0
    for b in batches:
        for t in b:
            for completion in (min(TYPICAL_COMPLETION_TOKENS, max_tokens), max_tokens):
                usd = rollout_usd(prompt_tokens[t], completion, model, train=True) + (prompt_tokens[t] + completion) * tp / 1e6
                if completion == max_tokens:
                    worst += usd
                else:
                    typ += usd
    n = sum(len(b) for b in batches) * group_size
    return {"rollouts": n, "typical_usd": round(typ * group_size, 2), "worst_usd": round(worst * group_size, 2)}


@app.command()
def train(
    model: str = typer.Option(DEFAULT_MODEL),
    teacher: str = typer.Option(DEFAULT_TEACHER),
    renderer_name: str = typer.Option(None, "--renderer"),
    from_run: str = typer.Option(None, help="Start from this run's checkpoint (default: the base model)."),
    steps: int = typer.Option(40),
    tasks_per_step: int = typer.Option(16),
    group_size: int = typer.Option(4),
    learning_rate: float = typer.Option(1e-4, help="The cookbook distillation recipe's default."),
    lora_rank: int = typer.Option(32),
    max_tokens: int = typer.Option(2048),
    kl_penalty_coef: float = typer.Option(1.0),
    eval_every: int = typer.Option(10),
    seed: int = typer.Option(0),
    name: str = typer.Option(None),
    max_spend: float = typer.Option(40.0),
    dry_run: bool = typer.Option(False, "--dry-run"),
    yes: bool = typer.Option(False, "--yes"),
) -> None:
    renderer_name = renderer_name or DEFAULT_RENDERERS.get(model)
    if renderer_name is None:
        raise typer.BadParameter(f"no default renderer for {model}; pass --renderer")
    parent = checkpoint_record(from_run) if from_run else None
    task_ids = sorted(t.id for t in train_tasks())
    batches = rl_env.plan_batches(task_ids, tasks_per_step, steps, seed)
    renderer = rl_env.make_renderer(model, renderer_name)
    prompt_tokens = {tid: renderer.build_generation_prompt(list(rl_env.task_messages(tid))).length for tid in task_ids}
    est = estimate(prompt_tokens, batches, group_size, max_tokens, model, teacher)
    dev_prompt = {t.id: renderer.build_generation_prompt(list(rl_env.task_messages(t.id))).length for t in eval_tinker.split_tasks("dev")}
    dev_est = eval_tinker.estimate(dev_prompt, model, 5, 4096)
    n_evals = (steps // eval_every if eval_every else 0) + 1
    plan = {"model": model, "teacher": teacher, "renderer": renderer_name, "start_from": parent["state_path"] if parent else "base model",
            "tasks": len(task_ids), "steps": steps, "tasks_per_step": tasks_per_step, "group_size": group_size, "rollouts": est["rollouts"],
            "learning_rate": learning_rate, "kl_penalty_coef": kl_penalty_coef, "max_tokens": max_tokens,
            "train_typical_usd": est["typical_usd"], "train_worst_usd": est["worst_usd"], "dev_evals": n_evals,
            "total_typical_usd": round(est["typical_usd"] + n_evals * dev_est["typical_usd"], 2),
            "total_worst_usd": round(est["worst_usd"] + n_evals * dev_est["worst_usd"], 2)}
    typer.echo(json.dumps(plan, indent=2))
    if dry_run:
        return
    if not yes:
        raise typer.BadParameter("this spends money: run with --dry-run first, then pass --yes")
    if plan["total_worst_usd"] > max_spend:
        raise typer.BadParameter(f"worst case ${plan['total_worst_usd']} exceeds --max-spend ${max_spend}")

    load_tinker_key()
    from tinker_cookbook.distillation import train_on_policy
    from tinker_cookbook.distillation.datasets import DistillationDatasetConfig, TeacherConfig

    run_id = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    slug = model.split("/")[-1]
    name = name or f"distil_{slug}_{run_id}"
    log_path = RESULTS_DIR / "runs" / name
    log_path.mkdir(parents=True, exist_ok=False)
    (log_path / "plan.json").write_text(json.dumps({**plan, "run_id": run_id, "seed": seed, "task_ids": task_ids}, indent=2) + "\n")
    guard = rl_env.spend_guard(name, max_spend=max_spend, **price(model))
    dataset_builder = rl_env.RlsDatasetBuilder(
        task_ids=task_ids, steps=steps, tasks_per_step=tasks_per_step, group_size=group_size, model_name=model,
        renderer_name=renderer_name, seed=seed, max_turns=1, max_tokens=max_tokens, guard_name=name, reward_scale=0.0)
    evaluator = rl_env.make_dev_evaluator(prefix=f"{slug}@{name}", model_name=model, renderer_name=renderer_name,
                                          log_path=log_path, max_spend=dev_est["worst_usd"] + 0.05)
    config = train_on_policy.Config(
        learning_rate=learning_rate, model_name=model, recipe_name="rls_bench_distil", renderer_name=renderer_name,
        max_tokens=max_tokens, log_path=str(log_path), eval_every=eval_every, save_every=eval_every or steps,
        evaluator_builders=[evaluator], load_checkpoint_path=parent["state_path"] if parent else None, lora_rank=lora_rank,
        kl_penalty_coef=kl_penalty_coef,
        dataset_configs=[DistillationDatasetConfig(dataset_builder=dataset_builder, teacher_config=TeacherConfig(base_model=teacher),
                                                   groups_per_batch=tasks_per_step)],
    )
    asyncio.run(train_on_policy.main(config))

    checkpoints = [json.loads(line) for line in (log_path / "checkpoints.jsonl").read_text().splitlines()]
    dev_path = log_path / "dev_evals.jsonl"
    dev_evals = [json.loads(line) for line in dev_path.read_text().splitlines()] if dev_path.exists() else []
    final = next((c for c in reversed(checkpoints) if c.get("sampler_path")), checkpoints[-1])
    best = max(dev_evals, key=lambda e: e["dev/pass_all"]) if dev_evals else None
    record = {"run_id": run_id, "kind": "distil", "framework": "cookbook", "name": name, "model": model, "teacher": teacher,
              "renderer": renderer_name, "parent_run_id": from_run, "lora_rank": lora_rank, "learning_rate": learning_rate,
              "kl_penalty_coef": kl_penalty_coef, "steps": steps, "tasks_per_step": tasks_per_step, "group_size": group_size,
              "max_tokens": max_tokens, "seed": seed, "tasks": task_ids,
              "est_spend_usd": round(guard.spent() + sum(e["dev/spend_usd"] for e in dev_evals), 4),
              "log_path": str(log_path.relative_to(ROOT)), "metrics": str((log_path / "metrics.jsonl").relative_to(ROOT)),
              "checkpoints": checkpoints, "dev_evals": dev_evals, "best_dev_eval": best,
              "state_path": final.get("state_path"), "sampler_path": final.get("sampler_path")}
    # teacher prefill is not seen by the guard: add it from the tokens the guard counted
    record["est_spend_usd"] = round(record["est_spend_usd"] + (guard.prompt_tokens + guard.completion_tokens) * price(teacher)["prefill"] / 1e6, 4)
    existing = json.loads(CHECKPOINTS_PATH.read_text()) if CHECKPOINTS_PATH.exists() else []
    CHECKPOINTS_PATH.write_text(json.dumps(existing + [record], indent=2) + "\n")
    typer.echo(json.dumps({k: record[k] for k in ("run_id", "name", "steps", "est_spend_usd", "best_dev_eval", "sampler_path")}, indent=2))


if __name__ == "__main__":
    app()
