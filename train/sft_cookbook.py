"""LoRA SFT on the cookbook's supervised loop, with a held-out dev loss (spec §8.2).

Train data: data/sft.jsonl (train tasks only). Dev data: data/sft_dev.jsonl (dev tasks only, built by
`build_sft.py dev-set`); the loop scores it every `eval_every` steps as `test/nll`. A learning-rate
sweep is a set of these runs; the run with the lowest final dev loss is the SFT model, so no retraining.

`--dry-run` tokenizes everything locally and prints the estimate; no Tinker call.
"""

from __future__ import annotations

import asyncio
import datetime as dt
import json
import warnings
from pathlib import Path
from typing import Any

import chz
import typer

warnings.filterwarnings("ignore", message=r'Field "model_')  # noisy pydantic warnings from tinker

from harness import split as splitmod  # noqa: E402
from harness.db import ROOT  # noqa: E402
from train.prices import price  # noqa: E402
from train.rl_cookbook import DEFAULT_MODEL, DEFAULT_RENDERERS, default_lr  # noqa: E402
from train.sft_tinker import CHECKPOINTS_PATH, RESULTS_DIR, data_hash, load_tinker_key  # noqa: E402

SFT_PATH = ROOT / "data" / "sft.jsonl"
DEV_PATH = ROOT / "data" / "sft_dev.jsonl"

app = typer.Typer(add_completion=False)


@app.callback()
def _cli() -> None:
    """Subcommands below."""


def _check_split(path: Path, allowed: set[str]) -> list[dict[str, Any]]:
    rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    bad = sorted({r["task_id"] for r in rows} - allowed)
    if bad:
        raise ValueError(f"{path.name} contains tasks outside its split: {bad}")
    return rows


def load_sets(train_path: Path = SFT_PATH, dev_path: Path = DEV_PATH) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    split = splitmod.load()
    return _check_split(train_path, set(split["train"])), _check_split(dev_path, set(split["dev"]))


def build_datums(rows, renderer, max_length: int):
    from tinker_cookbook import renderers
    from tinker_cookbook.supervised.data import conversation_to_datum

    datums = [conversation_to_datum(r["messages"], renderer, max_length, renderers.TrainOnWhat.LAST_ASSISTANT_MESSAGE) for r in rows]
    return datums, {"examples": len(rows), "tokens": sum(d.model_input.length for d in datums),
                    "max_tokens": max(d.model_input.length for d in datums)}


from tinker_cookbook.supervised.types import ChatDatasetBuilder, SupervisedDataset  # noqa: E402


@chz.chz
class RlsSftDatasetBuilder(ChatDatasetBuilder):
    """Train from data/sft.jsonl, dev from data/sft_dev.jsonl (or other files); both checked against the frozen split."""

    train_path: str = str(SFT_PATH)
    dev_path: str = str(DEV_PATH)

    def __call__(self) -> tuple[SupervisedDataset, SupervisedDataset | None]:
        import datasets
        from tinker_cookbook import renderers
        from tinker_cookbook.supervised.data import SupervisedDatasetFromHFDataset, conversation_to_datum

        train_rows, dev_rows = load_sets(Path(self.train_path), Path(self.dev_path))
        renderer = self.renderer

        def map_fn(row: dict) -> Any:
            return conversation_to_datum(row["messages"], renderer, self.common_config.max_length,
                                         renderers.TrainOnWhat.LAST_ASSISTANT_MESSAGE)

        train = SupervisedDatasetFromHFDataset(datasets.Dataset.from_list([{"messages": r["messages"]} for r in train_rows]),
                                               batch_size=self.common_config.batch_size, map_fn=map_fn)
        dev = SupervisedDatasetFromHFDataset(datasets.Dataset.from_list([{"messages": r["messages"]} for r in dev_rows]),
                                             batch_size=len(dev_rows), map_fn=map_fn)
        return train, dev


def run_one(model: str, renderer_name: str, learning_rate: float, *, epochs: int, batch_size: int, max_length: int,
            lora_rank: int, eval_every: int, name: str, train_path: Path = SFT_PATH, dev_path: Path = DEV_PATH,
            recipe: str = "rls_bench_sft", log=print) -> dict[str, Any]:
    """One SFT run on the cookbook loop; returns the record appended to results/train/checkpoints.json."""
    from tinker_cookbook.supervised import train as sl_train
    from tinker_cookbook.supervised.types import ChatDatasetBuilderCommonConfig

    run_id = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    log_path = RESULTS_DIR / "runs" / name
    log_path.mkdir(parents=True, exist_ok=False)
    builder = RlsSftDatasetBuilder(train_path=str(train_path), dev_path=str(dev_path), common_config=ChatDatasetBuilderCommonConfig(
        model_name_for_tokenizer=model, renderer_name=renderer_name, max_length=max_length, batch_size=batch_size))
    config = sl_train.Config(
        log_path=str(log_path), model_name=model, recipe_name=recipe, renderer_name=renderer_name,
        dataset_builder=builder, learning_rate=learning_rate, lr_schedule="linear", num_epochs=epochs,
        lora_rank=lora_rank, eval_every=eval_every, save_every=0, ttl_seconds=None,
    )
    asyncio.run(sl_train.main(config))

    metrics = [json.loads(line) for line in (log_path / "metrics.jsonl").read_text().splitlines()]
    nll = [(m.get("step"), m["test/nll"]) for m in metrics if "test/nll" in m]
    train_nll = [m["train_mean_nll"] for m in metrics if "train_mean_nll" in m]
    checkpoints = [json.loads(line) for line in (log_path / "checkpoints.jsonl").read_text().splitlines()]
    final = next(c for c in reversed(checkpoints) if c.get("sampler_path"))
    record = {
        "run_id": run_id, "kind": "sft", "framework": "cookbook", "name": name, "model": model, "renderer": renderer_name,
        "lora_rank": lora_rank, "learning_rate": learning_rate, "epochs": epochs, "batch_size": batch_size,
        "max_length": max_length, "recipe": recipe, "train_path": str(train_path.relative_to(ROOT)),
        "data_hash": data_hash(train_path), "dev_data_hash": data_hash(dev_path),
        "steps": len(train_nll), "dev_nll": nll, "final_dev_nll": nll[-1][1] if nll else None,
        "min_dev_nll": min(v for _, v in nll) if nll else None,
        "first_train_nll": train_nll[0] if train_nll else None, "last_train_nll": train_nll[-1] if train_nll else None,
        "log_path": str(log_path.relative_to(ROOT)), "metrics": str((log_path / "metrics.jsonl").relative_to(ROOT)),
        "state_path": final.get("state_path"), "sampler_path": final.get("sampler_path"),
    }
    existing = json.loads(CHECKPOINTS_PATH.read_text()) if CHECKPOINTS_PATH.exists() else []
    CHECKPOINTS_PATH.write_text(json.dumps(existing + [record], indent=2) + "\n")
    log(json.dumps({k: record[k] for k in ("run_id", "name", "learning_rate", "steps", "final_dev_nll", "min_dev_nll")}))
    return record


def plan(model: str, renderer_name: str, lrs: list[float], epochs: int, batch_size: int, max_length: int,
         train_path: Path = SFT_PATH) -> dict[str, Any]:
    from train.sft_tinker import make_renderer

    train_rows, dev_rows = load_sets(train_path)
    renderer, _ = make_renderer(model, renderer_name)
    _, train_stats = build_datums(train_rows, renderer, max_length)
    _, dev_stats = build_datums(dev_rows, renderer, max_length)
    steps = (train_stats["examples"] // batch_size) * epochs
    train_tokens = train_stats["tokens"] * epochs
    evals = steps // 10 + 2
    p = price(model)
    per_run = (train_tokens * p["train"] + evals * dev_stats["tokens"] * p["prefill"]) / 1e6
    return {"model": model, "renderer": renderer_name, "train_path": str(train_path.relative_to(ROOT)), "learning_rates": lrs, "epochs": epochs, "batch_size": batch_size,
            "steps_per_run": steps, "train": train_stats, "dev": dev_stats, "train_tokens_per_run": train_tokens,
            "usd_per_run": round(per_run, 3), "usd_total": round(per_run * len(lrs), 3)}


@app.command()
def sweep(
    model: str = typer.Option(DEFAULT_MODEL),
    renderer_name: str = typer.Option(None, "--renderer"),
    train_path: Path = typer.Option(SFT_PATH, "--train-path", help="Training file (train tasks only)."),
    tag: str = typer.Option("", help="Suffix for run names and the sweep file, e.g. v3."),
    lrs: str = typer.Option(None, "--lrs", help="Comma-separated; default: calibrated rate x (0.33, 1, 3)."),
    epochs: int = typer.Option(3),
    batch_size: int = typer.Option(16),
    max_length: int = typer.Option(4096),
    lora_rank: int = typer.Option(32),
    eval_every: int = typer.Option(10),
    max_spend: float = typer.Option(15.0),
    dry_run: bool = typer.Option(False, "--dry-run"),
    yes: bool = typer.Option(False, "--yes"),
) -> None:
    renderer_name = renderer_name or DEFAULT_RENDERERS.get(model)
    if renderer_name is None:
        raise typer.BadParameter(f"no default renderer for {model}; pass --renderer")
    if lrs:
        rates = [float(x) for x in lrs.split(",")]
    else:
        base = default_lr(model)
        if base is None:
            raise typer.BadParameter(f"no calibrated rate for {model}; pass --lrs")
        rates = [round(base / 3, 7), round(base, 7), round(base * 3, 7)]
    p = plan(model, renderer_name, rates, epochs, batch_size, max_length, train_path)
    typer.echo(json.dumps(p, indent=2))
    if dry_run:
        return
    if not yes:
        raise typer.BadParameter("this spends money: run with --dry-run first, then pass --yes")
    if p["usd_total"] > max_spend:
        raise typer.BadParameter(f"estimated ${p['usd_total']} exceeds --max-spend ${max_spend}")
    load_tinker_key()
    slug = model.split("/")[-1]
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    records = []
    for lr in rates:
        records.append(run_one(model, renderer_name, lr, epochs=epochs, batch_size=batch_size, max_length=max_length,
                               lora_rank=lora_rank, eval_every=eval_every, name=f"sft{tag and '_' + tag}_{slug}_{stamp}_lr{lr:g}",
                               train_path=train_path, log=typer.echo))
    best = min(records, key=lambda r: r["final_dev_nll"])
    out = {"model": model, "sweep_id": stamp, "train_path": str(train_path.relative_to(ROOT)), "runs": [{k: r[k] for k in ("run_id", "name", "learning_rate", "final_dev_nll", "min_dev_nll", "last_train_nll")} for r in records],
           "best_run_id": best["run_id"], "best_learning_rate": best["learning_rate"], "best_final_dev_nll": best["final_dev_nll"]}
    (RESULTS_DIR / f"sft_sweep{tag and '_' + tag}_{slug}_{stamp}.json").write_text(json.dumps(out, indent=2) + "\n")
    typer.echo(json.dumps(out, indent=2))


if __name__ == "__main__":
    app()
