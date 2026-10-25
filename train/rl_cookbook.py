"""GRPO on the cookbook's RL loop with the harness as the environment (train/rl_env.py).

Replaces the hand-rolled loop in train/rl_tinker.py: sampling and training are pipelined by the
cookbook, a dev evaluator runs on every saved checkpoint, and the standard training-health metrics
(reward, sampler-vs-trainer KL, entropy, lengths) are logged to <log_path>/metrics.jsonl.

`--dry-run` plans the batches, checks the reward on every task's reference and traps through the
environment, and prints the cost estimate. It makes no Tinker call.
"""

from __future__ import annotations

import asyncio
import datetime as dt
import json
import warnings
from pathlib import Path
from typing import Any

import typer

warnings.filterwarnings("ignore", message=r'Field "model_')  # noisy pydantic warnings from tinker

from harness.db import ROOT  # noqa: E402
from train import eval_tinker, rl_env  # noqa: E402
from train.build_sft import train_tasks  # noqa: E402
from train.prices import price, rollout_usd  # noqa: E402
from train.sft_tinker import CHECKPOINTS_PATH, RESULTS_DIR, load_tinker_key  # noqa: E402

DEFAULT_MODEL = "Qwen/Qwen3.5-9B"
DEFAULT_RENDERERS = {
    "Qwen/Qwen3.5-9B": "qwen3_5_disable_thinking",
    "Qwen/Qwen3-8B": "qwen3_disable_thinking",
    "nvidia/NVIDIA-Nemotron-3.5-Lightning-30B-A3B-BF16": "nemotron3_ultra_disable_thinking",
}
TYPICAL_COMPLETION_TOKENS = 700
FEEDBACK_TOKENS = 250  # a feedback message plus chat framing, for multi-turn estimates

app = typer.Typer(add_completion=False)


@app.callback()
def _cli() -> None:
    """Subcommands below."""


def default_lr(model: str) -> float | None:
    from tinker_cookbook import hyperparam_utils

    try:
        return hyperparam_utils.get_lr(model)
    except NotImplementedError:
        return None


def checkpoint_record(run_id: str) -> dict[str, Any]:
    records = [r for r in json.loads(CHECKPOINTS_PATH.read_text()) if r["run_id"] == run_id]
    if not records:
        raise typer.BadParameter(f"no run {run_id} in {CHECKPOINTS_PATH.relative_to(ROOT)}")
    return records[-1]


def estimate(prompt_tokens: dict[str, int], batches: list[list[str]], group_size: int, max_tokens: int,
             max_turns: int, model: str) -> dict[str, Any]:
    """Sampling + training cost. Multi-turn: every turn re-reads the growing conversation."""
    def episode(prompt: int, completion: int, turns: int) -> float:
        usd = 0.0
        for turn in range(turns):
            ctx = prompt + turn * (completion + FEEDBACK_TOKENS)
            usd += rollout_usd(ctx, completion, model, train=True)
        return usd

    typical = sum(episode(prompt_tokens[t], min(TYPICAL_COMPLETION_TOKENS, max_tokens), min(2, max_turns))
                  for b in batches for t in b) * group_size
    worst = sum(episode(prompt_tokens[t], max_tokens, max_turns) for b in batches for t in b) * group_size
    return {"rollouts": sum(len(b) for b in batches) * group_size, "typical_usd": round(typical, 2),
            "worst_usd": round(worst, 2)}


async def reward_check(task_ids: list[str], max_turns: int, leak_penalty: float) -> dict[str, Any]:
    """Run every reference and trap through the environment (no sampling): references must score 1."""
    problems, trap_rewards, references = [], {}, 0
    for tid in task_ids:
        task = rl_env.load_task(tid)
        env = rl_env.RlsMessageEnv(task, renderer=None, max_turns=1, leak_penalty=leak_penalty)
        step = await env.step({"role": "assistant", "content": f"```sql\n{task.solution_sql}\n```"})
        references += step.reward == 1.0
        if step.reward != 1.0:
            problems.append({"task": tid, "reference_reward": step.reward})
        for trap in sorted((task.path / "traps").glob("*.sql")):
            env = rl_env.RlsMessageEnv(task, renderer=None, max_turns=max_turns, leak_penalty=leak_penalty)
            step = await env.step({"role": "assistant", "content": f"```sql\n{trap.read_text()}\n```"})
            trap_rewards[str(step.reward)] = trap_rewards.get(str(step.reward), 0) + 1
            if step.reward >= 1.0:
                problems.append({"task": tid, "trap": trap.stem, "reward": step.reward})
            if max_turns > 1 and step.episode_done:
                problems.append({"task": tid, "trap": trap.stem, "note": "episode ended after a failing first turn"})
    return {"tasks": len(task_ids), "references_scoring_1": references, "trap_rewards": trap_rewards, "problems": problems}


@app.command()
def train(
    model: str = typer.Option(DEFAULT_MODEL),
    renderer_name: str = typer.Option(None, "--renderer"),
    from_run: str = typer.Option(None, help="Start from this run's checkpoint (run_id in results/train/checkpoints.json)."),
    from_path: str = typer.Option(None, help="Start from an explicit tinker:// state path."),
    steps: int = typer.Option(60),
    tasks_per_step: int = typer.Option(24),
    group_size: int = typer.Option(8),
    learning_rate: float = typer.Option(None, help="Default: the cookbook's calibrated LoRA rate for the model."),
    lora_rank: int = typer.Option(32),
    max_tokens: int = typer.Option(2048),
    max_turns: int = typer.Option(1, help="1 = single answer; >1 = repair turns with harness feedback."),
    leak_penalty: float = typer.Option(rl_env.LEAK_PENALTY),
    turn_penalty: float = typer.Option(rl_env.TURN_PENALTY),
    eval_every: int = typer.Option(10, help="Dev eval and checkpoint every N steps (0 = final only)."),
    seed: int = typer.Option(0),
    name: str = typer.Option(None, help="Run label; default rl_<model>_<timestamp>."),
    max_spend: float = typer.Option(40.0, help="Hard stop (estimated USD) for the whole run."),
    dry_run: bool = typer.Option(False, "--dry-run"),
    yes: bool = typer.Option(False, "--yes"),
) -> None:
    renderer_name = renderer_name or DEFAULT_RENDERERS.get(model)
    if renderer_name is None:
        raise typer.BadParameter(f"no default renderer for {model}; pass --renderer")
    learning_rate = learning_rate or default_lr(model)
    if learning_rate is None:
        raise typer.BadParameter(f"the cookbook has no calibrated LoRA learning rate for {model}; pass --learning-rate")
    if from_run and from_path:
        raise typer.BadParameter("pass --from-run or --from-path, not both")
    parent = checkpoint_record(from_run) if from_run else None
    load_path = parent["state_path"] if parent else from_path
    if parent and parent["model"] != model:
        raise typer.BadParameter(f"run {from_run} is a {parent['model']} checkpoint, not {model}")

    task_ids = sorted(t.id for t in train_tasks())
    batches = rl_env.plan_batches(task_ids, tasks_per_step, steps, seed)
    renderer = rl_env.make_renderer(model, renderer_name)
    prompt_tokens = {tid: renderer.build_generation_prompt(list(rl_env.task_messages(tid))).length for tid in task_ids}
    est = estimate(prompt_tokens, batches, group_size, max_tokens, max_turns, model)
    dev_prompt = {t.id: renderer.build_generation_prompt(list(rl_env.task_messages(t.id))).length
                  for t in eval_tinker.split_tasks("dev")}
    dev_est = eval_tinker.estimate(dev_prompt, model, 5, 4096) if model in eval_tinker.SAMPLE_PRICES else {"typical_usd": 0, "worst_usd": 0}
    n_evals = (steps // eval_every if eval_every else 0) + 1
    plan = {
        "model": model, "renderer": renderer_name, "start_from": load_path or "base model", "tasks": len(task_ids),
        "steps": steps, "tasks_per_step": tasks_per_step, "group_size": group_size, "rollouts": est["rollouts"],
        "epochs": round(steps * tasks_per_step / len(task_ids), 2), "learning_rate": learning_rate, "lora_rank": lora_rank,
        "max_tokens": max_tokens, "max_turns": max_turns, "leak_penalty": leak_penalty, "turn_penalty": turn_penalty,
        "mean_prompt_tokens": round(sum(prompt_tokens.values()) / len(prompt_tokens)),
        "train_typical_usd": est["typical_usd"], "train_worst_usd": est["worst_usd"],
        "dev_evals": n_evals, "dev_eval_typical_usd": round(dev_est["typical_usd"], 3), "dev_eval_worst_usd": round(dev_est["worst_usd"], 3),
        "total_typical_usd": round(est["typical_usd"] + n_evals * dev_est["typical_usd"], 2),
        "total_worst_usd": round(est["worst_usd"] + n_evals * dev_est["worst_usd"], 2),
    }
    typer.echo(json.dumps(plan, indent=2))
    if dry_run:
        typer.echo(json.dumps({"reward_check": asyncio.run(reward_check(task_ids, max_turns, leak_penalty))}, indent=2))
        return
    if not yes:
        raise typer.BadParameter("this spends money: run with --dry-run first, then pass --yes")
    if plan["total_worst_usd"] > max_spend:
        raise typer.BadParameter(f"worst case ${plan['total_worst_usd']} exceeds --max-spend ${max_spend}; shrink the run")

    load_tinker_key()
    from tinker_cookbook.rl import train as rl_train

    run_id = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    slug = model.split("/")[-1]
    name = name or f"rl_{slug}_{run_id}"
    log_path = RESULTS_DIR / "runs" / name
    log_path.mkdir(parents=True, exist_ok=False)
    (log_path / "plan.json").write_text(json.dumps({**plan, "run_id": run_id, "seed": seed, "task_ids": task_ids,
                                                     "max_spend": max_spend}, indent=2) + "\n")
    guard = rl_env.spend_guard(name, max_spend=max_spend, **price(model))
    dataset_builder = rl_env.RlsDatasetBuilder(
        task_ids=task_ids, steps=steps, tasks_per_step=tasks_per_step, group_size=group_size, model_name=model,
        renderer_name=renderer_name, seed=seed, max_turns=max_turns, leak_penalty=leak_penalty,
        turn_penalty=turn_penalty, max_tokens=max_tokens, guard_name=name)
    if max_turns > 1:
        from train.repair_eval import RepairDevEvaluator

        dev_evaluator = RepairDevEvaluator(prefix=f"{slug}@{name}", model_name=model, renderer_name=renderer_name,
                                           log_path=log_path, max_turns=max_turns, max_spend=max_turns * dev_est["worst_usd"] + 0.05)
        evaluator = lambda: dev_evaluator  # noqa: E731
    else:
        evaluator = rl_env.make_dev_evaluator(prefix=f"{slug}@{name}", model_name=model, renderer_name=renderer_name,
                                              log_path=log_path, max_spend=dev_est["worst_usd"] + 0.05)
    config = rl_train.Config(
        learning_rate=learning_rate, dataset_builder=dataset_builder, model_name=model, recipe_name="rls_bench_grpo",
        max_tokens=max_tokens, log_path=str(log_path), eval_every=eval_every, save_every=eval_every or steps,
        evaluator_builders=[evaluator], load_checkpoint_path=load_path, renderer_name=renderer_name,
        lora_rank=lora_rank, temperature=1.0, remove_constant_reward_groups=True, ttl_seconds=None,
    )
    asyncio.run(rl_train.main(config))

    checkpoints = [json.loads(line) for line in (log_path / "checkpoints.jsonl").read_text().splitlines()]
    dev_path = log_path / "dev_evals.jsonl"
    dev_evals = [json.loads(line) for line in dev_path.read_text().splitlines()] if dev_path.exists() else []
    final = next((c for c in reversed(checkpoints) if c.get("sampler_path")), checkpoints[-1])
    best = max(dev_evals, key=lambda e: e.get("dev/pass_final", e["dev/pass_all"])) if dev_evals else None
    record = {
        "run_id": run_id, "kind": "rl", "framework": "cookbook", "name": name, "model": model, "renderer": renderer_name,
        "parent_run_id": from_run, "load_checkpoint_path": load_path, "lora_rank": lora_rank, "learning_rate": learning_rate,
        "steps": steps, "tasks_per_step": tasks_per_step, "group_size": group_size, "max_tokens": max_tokens,
        "max_turns": max_turns, "leak_penalty": leak_penalty, "turn_penalty": turn_penalty, "seed": seed,
        "tasks": task_ids, "est_spend_usd": round(guard.spent() + sum(e["dev/spend_usd"] for e in dev_evals), 4),
        "log_path": str(log_path.relative_to(ROOT)), "metrics": str((log_path / "metrics.jsonl").relative_to(ROOT)),
        "checkpoints": checkpoints, "dev_evals": dev_evals, "best_dev_eval": best,
        "state_path": final.get("state_path"), "sampler_path": final.get("sampler_path"),
    }
    existing = json.loads(CHECKPOINTS_PATH.read_text()) if CHECKPOINTS_PATH.exists() else []
    CHECKPOINTS_PATH.write_text(json.dumps(existing + [record], indent=2) + "\n")
    typer.echo(json.dumps({k: record[k] for k in ("run_id", "name", "steps", "est_spend_usd", "best_dev_eval", "sampler_path")}, indent=2))


if __name__ == "__main__":
    app()
