"""LoRA SFT on Tinker from data/sft.jsonl (spec §8.2), following the cookbook's sl_loop recipe.

`--dry-run` tokenizes every example locally with the model's renderer and prints exact token
counts and a cost estimate. It never creates a Tinker client, so it spends nothing.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import logging
import random
import time
import warnings
from pathlib import Path
from typing import Any

import typer

warnings.filterwarnings("ignore", message=r'Field "model_')  # noisy pydantic warnings from tinker

from harness import split as splitmod  # noqa: E402
from harness.db import ROOT  # noqa: E402

SFT_PATH = ROOT / "data" / "sft.jsonl"
RESULTS_DIR = ROOT / "results" / "train"
CHECKPOINTS_PATH = RESULTS_DIR / "checkpoints.json"

DEFAULT_MODEL = "nvidia/NVIDIA-Nemotron-3.5-Lightning-30B-A3B-BF16"
# Reasoning off, matching the reasoning-off baseline; must be one of the cookbook's recommended
# renderers for the model (checked at startup).
DEFAULT_RENDERER = "nemotron3_ultra_disable_thinking"
# The cookbook has no calibrated LoRA learning rate for Nemotron (hyperparam_utils.get_lr raises
# NotImplementedError); 1e-4 is the cookbook's minimal-SFT recipe default.
DEFAULT_LR = 1e-4

# Tinker list prices, USD per 1M tokens, from thinkingmachines.ai/tinker/pricing as of 2026-10-19
# (Nemotron-3.5-Lightning shown at 50% off). Recheck before large runs.
TRAIN_PRICE_PER_M = {"nvidia/NVIDIA-Nemotron-3.5-Lightning-30B-A3B-BF16": 0.44, "Qwen/Qwen3-8B": 0.44}

log = logging.getLogger("sft_tinker")
app = typer.Typer(add_completion=False)


def load_examples(path: Path) -> list[dict[str, Any]]:
    rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    split = splitmod.load()
    held_out = set(split["dev"]) | set(split["test"])
    leaked = sorted({r["task_id"] for r in rows} & held_out)
    if leaked:
        raise ValueError(f"SFT data contains dev/test tasks: {leaked}")
    return rows


def make_renderer(model: str, renderer_name: str):
    from tinker_cookbook import model_info, renderers
    from tinker_cookbook.tokenizer_utils import get_tokenizer

    recommended = model_info.get_recommended_renderer_names(model)
    if renderer_name not in recommended:
        raise typer.BadParameter(f"renderer {renderer_name!r} is not recommended for {model}: {recommended}")
    tokenizer = get_tokenizer(model)
    return renderers.get_renderer(renderer_name, tokenizer), tokenizer


def build_datums(rows: list[dict[str, Any]], renderer, max_length: int):
    from tinker_cookbook import renderers
    from tinker_cookbook.supervised.data import conversation_to_datum

    datums, stats = [], {"examples": len(rows), "tokens": 0, "trained_tokens": 0, "truncated": 0, "max_tokens": 0}
    for row in rows:
        full = conversation_to_datum(row["messages"], renderer, None, renderers.TrainOnWhat.LAST_ASSISTANT_MESSAGE)
        if full.model_input.length > max_length:
            stats["truncated"] += 1
        datum = conversation_to_datum(row["messages"], renderer, max_length, renderers.TrainOnWhat.LAST_ASSISTANT_MESSAGE)
        weights = datum.loss_fn_inputs["weights"]
        n = datum.model_input.length
        stats["tokens"] += n
        stats["trained_tokens"] += sum(1 for w in weights.tolist() if w > 0)
        stats["max_tokens"] = max(stats["max_tokens"], n)
        datums.append(datum)
    return datums, stats


def plan_steps(n_examples: int, batch_size: int, epochs: int) -> int:
    return (n_examples // batch_size) * epochs


def estimate(stats: dict[str, Any], model: str, epochs: int, batch_size: int) -> dict[str, Any]:
    price = TRAIN_PRICE_PER_M[model]
    used_per_epoch = stats["tokens"] * ((stats["examples"] // batch_size) * batch_size) / stats["examples"]
    train_tokens = used_per_epoch * epochs
    return {"train_tokens": int(train_tokens), "price_per_m": price, "train_usd": train_tokens / 1e6 * price}


def data_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16]


@app.command()
def main(
    model: str = typer.Option(DEFAULT_MODEL),
    renderer_name: str = typer.Option(DEFAULT_RENDERER, "--renderer"),
    data: Path = typer.Option(SFT_PATH),
    lora_rank: int = typer.Option(32),
    learning_rate: float = typer.Option(DEFAULT_LR),
    epochs: int = typer.Option(3),
    batch_size: int = typer.Option(16),
    max_length: int = typer.Option(4096),
    seed: int = typer.Option(0),
    max_spend: float = typer.Option(10.0, help="Stop before a step that would push estimated spend past this (USD)."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Tokenize locally and print the estimate; no Tinker calls."),
    yes: bool = typer.Option(False, "--yes", help="Confirm the spend."),
) -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    rows = load_examples(data)
    renderer, _ = make_renderer(model, renderer_name)
    datums, stats = build_datums(rows, renderer, max_length)
    steps = plan_steps(len(datums), batch_size, epochs)
    est = estimate(stats, model, epochs, batch_size)
    typer.echo(json.dumps({"model": model, "renderer": renderer_name, "data": str(data.relative_to(ROOT)),
                           "data_hash": data_hash(data), "steps": steps, **stats, **est}, indent=2))
    if dry_run:
        return
    if not yes:
        raise typer.BadParameter("this spends money: run with --dry-run first, then pass --yes")

    import tinker
    from tinker_cookbook import checkpoint_utils
    from tinker_cookbook.supervised.common import compute_mean_nll

    run_id = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    slug = model.split("/")[-1]
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    metrics_path = RESULTS_DIR / f"sft_{slug}_{run_id}.jsonl"
    log_path = RESULTS_DIR / "runs" / f"sft_{slug}_{run_id}"
    log_path.mkdir(parents=True, exist_ok=True)

    service = tinker.ServiceClient()
    training_client = service.create_lora_training_client(base_model=model, rank=lora_rank)
    price = TRAIN_PRICE_PER_M[model]
    rng = random.Random(seed)
    order = list(range(len(datums)))
    spent, step, stopped = 0.0, 0, False
    for epoch in range(epochs):
        rng.shuffle(order)
        for b in range(len(order) // batch_size):
            batch = [datums[i] for i in order[b * batch_size:(b + 1) * batch_size]]
            batch_tokens = sum(d.model_input.length for d in batch)
            if spent + batch_tokens / 1e6 * price > max_spend:
                stopped = True
                break
            lr = learning_rate * max(0.0, 1.0 - step / steps)
            started = time.time()
            fb = training_client.forward_backward(batch, loss_fn="cross_entropy")
            opt = training_client.optim_step(tinker.AdamParams(learning_rate=lr, beta1=0.9, beta2=0.95, eps=1e-8))
            fb_result, _ = fb.result(), opt.result()
            nll = compute_mean_nll([x["logprobs"] for x in fb_result.loss_fn_outputs], [d.loss_fn_inputs["weights"] for d in batch])
            spent += batch_tokens / 1e6 * price
            row = {"step": step, "epoch": epoch, "lr": lr, "train_mean_nll": nll, "tokens": batch_tokens,
                   "est_spend_usd": round(spent, 4), "seconds": round(time.time() - started, 2)}
            with metrics_path.open("a") as f:
                f.write(json.dumps(row) + "\n")
            log.info(json.dumps(row))
            step += 1
        if stopped:
            log.info(f"spend cap ${max_spend:.2f} reached after {step} steps")
            break

    paths = checkpoint_utils.save_checkpoint(training_client=training_client, name="final", log_path=str(log_path),
                                             kind="both", loop_state={"step": step}, ttl_seconds=None)
    record = {"run_id": run_id, "kind": "sft", "model": model, "renderer": renderer_name, "lora_rank": lora_rank,
              "learning_rate": learning_rate, "epochs": epochs, "batch_size": batch_size, "max_length": max_length,
              "seed": seed, "data_hash": data_hash(data), "examples": len(datums), "steps": step,
              "stopped_at_cap": stopped, "est_spend_usd": round(spent, 4), "metrics": str(metrics_path.relative_to(ROOT)),
              **paths}
    existing = json.loads(CHECKPOINTS_PATH.read_text()) if CHECKPOINTS_PATH.exists() else []
    CHECKPOINTS_PATH.write_text(json.dumps(existing + [record], indent=2) + "\n")
    typer.echo(json.dumps(record, indent=2))


if __name__ == "__main__":
    app()
