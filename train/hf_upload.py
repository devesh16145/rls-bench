"""Publish the task set and the exported adapters on Hugging Face.

`build` stages the dataset (one JSONL per split plus the task directories as the harness reads them) and
renders both repo cards from `docs/hf/*.md`, filling the tables from `results/`. `upload` builds and then
pushes to the two repos. Needs a write token as `HF_TOKEN` in `.env`. Nothing here spends Tinker or
OpenRouter credit.
"""

from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

import typer

from harness import split as split_mod
from harness.db import ROOT
from harness.models import Task

TASKS_DIR = ROOT / "tasks"
RESULTS_DIR = ROOT / "results"
TRAIN_DIR = RESULTS_DIR / "train"
ADAPTERS_DIR = TRAIN_DIR / "adapters"
CARDS_DIR = ROOT / "docs" / "hf"
STAGING_DIR = ROOT / ".rlsbench" / "hf_dataset"  # gitignored

HF_USER = "9eve5h"
DATASET_REPO = f"{HF_USER}/rls-bench"
ADAPTERS_REPO = f"{HF_USER}/rls-bench-adapters"

# (folder under results/train/adapters, test-eval directory, model key in its summary.json, what it is)
ADAPTERS: list[tuple[str, str, str, str]] = [
    ("sft_Qwen3.5-9B", "test_eval_v2", "sft",
     "SFT on 427 passing DeepSeek V4.1 Flash answers to the 72 train tasks (version 2 data)"),
    ("grpo_Qwen3.5-9B_step40", "test_eval_v2", "sft+rl",
     "GRPO from the SFT model, seed 0, step 40 of 50"),
    ("grpo_Qwen3.5-9B_seed1_step40", "test_eval_v2", "sft+rl-seed1",
     "GRPO from the SFT model, seed 1, step 40 of 50"),
    ("repair_Qwen3.5-9B_step5", "test_eval_v2", "repair",
     "repair RL (up to three tries with harness feedback) from the GRPO seed-0 step-40 checkpoint, step 5 of 25"),
    ("distil_Qwen3.5-9B_step30", "test_eval_v2", "distil",
     "on-policy distillation from Qwen3.5-397B-A17B with no correctness signal, step 30 of 40"),
    ("sft_v3_Qwen3.5-9B", "test_eval_v3", "sft-v3",
     "SFT on two-source data (DeepSeek V4.1 Flash and Kimi K2.6), 72 train tasks (version 3 data)"),
    ("grpo_v3_Qwen3.5-9B_step40", "test_eval_v3", "sft-v3+rl",
     "GRPO from the version-3 SFT model, seed 0, step 40 of 40"),
    ("sft_82tasks_Qwen3.5-9B", "test_eval_v4", "sft-82",
     "SFT on two-source data, 82 train tasks (version 4)"),
    ("grpo_v5_halfbatch_Qwen3.5-9B_step10", "test_eval_v5", "sft-82+rl",
     "GRPO from the version-4 SFT model at half batch, step 10 of 40 (a negative result: worse than its SFT)"),
    ("sft_Nemotron", "test_eval_v2", "nemotron-sft",
     "SFT on the version 2 data"),
    ("grpo_Nemotron_step50", "test_eval_v2", "nemotron-sft+rl",
     "GRPO from the SFT model, final checkpoint (step 50)"),
]
# untrained students evaluated the same way, for reference: (base model, test-eval directory, key)
BASE_ROWS: list[tuple[str, str, str]] = [
    ("Qwen/Qwen3.5-9B", "test_eval_v2", "base"),
    ("nvidia/NVIDIA-Nemotron-3.5-Lightning-30B-A3B-BF16", "test_eval_v2", "nemotron-base"),
]
JUDGE_FOLDER, JUDGE_KEY = "judge_Qwen3-8B", "trained_Qwen3-8B_20261025T185503Z"

app = typer.Typer(add_completion=False, no_args_is_help=True)


def load_hf_token() -> str:
    """HF_TOKEN from the environment or .env; never printed."""
    tok = os.environ.get("HF_TOKEN")
    if not tok:
        env_file = ROOT / ".env"
        if env_file.exists():
            for line in env_file.read_text().splitlines():
                name, sep, value = line.partition("=")
                if sep and name.strip() == "HF_TOKEN":
                    tok = value.strip().strip('"').strip("'")
    if not tok:
        raise typer.BadParameter("HF_TOKEN is not set (put a write token in .env)")
    return tok


# --- dataset -------------------------------------------------------------------------------------


def task_rows() -> list[dict]:
    """One row per task directory, with every file's contents and the task's split."""
    split = split_mod.load()
    where = {tid: name for name in ("train", "dev", "test") for tid in split[name]}
    rows = []
    for path in sorted(p for p in TASKS_DIR.glob("T*") if (p / "task.yaml").exists()):
        t = Task.load(path)
        if t.id not in where:
            raise ValueError(f"{t.id} is not in tasks/split.json; verify it and extend the train split first")
        rows.append({
            "id": t.id,
            "title": t.meta.title,
            "tier": t.meta.tier,
            "split": where[t.id],
            "tags": t.meta.tags,
            "traps": t.meta.traps,
            "extra_tables": t.meta.extra_tables,
            "fixture_notes": t.meta.fixture_notes,
            "created": t.meta.created.isoformat(),
            "canary": t.meta.canary,
            "requirement": t.requirement,
            "schema_sql": t.schema_sql,
            "seed_sql": t.seed_sql,
            "tests_yaml": (path / "tests.yaml").read_text(),
            "n_tests": len(t.tests),
            "solution_sql": t.solution_sql,
            "trap_files": [{"name": name, "sql": sql} for name, sql in t.trap_sql.items()],
        })
    return rows


def split_table(rows: list[dict]) -> str:
    """Per-tier counts from the tasks themselves (split.json's per_tier records only the original freeze)."""
    split = split_mod.load()
    names = ("train", "dev", "test")
    lines = ["| Tier | Train | Dev | Test | Total |", "|---|---|---|---|---|"]
    for tier in sorted({r["tier"] for r in rows}):
        c = {n: sum(1 for r in rows if r["tier"] == tier and r["split"] == n) for n in names}
        lines.append(f"| {tier} | {c['train']} | {c['dev']} | {c['test']} | {sum(c.values())} |")
    c = {n: sum(1 for r in rows if r["split"] == n) for n in names}
    if c != split["counts"]:
        raise ValueError(f"task directories {c} disagree with tasks/split.json {split['counts']}")
    lines.append(f"| **All** | **{c['train']}** | **{c['dev']}** | **{c['test']}** | **{sum(c.values())}** |")
    notes = [f"Frozen on {split['frozen_on']} (seed {split['seed']}; {split['method']})."]
    for rev in split.get("revisions", []):
        ids = rev["added_to_train"]
        notes.append(f"Revision on {rev['on']}: {ids[0]}–{ids[-1]} added to the train split ({rev['note']}).")
    return "\n".join(lines) + "\n\n" + " ".join(notes)


# --- adapters ------------------------------------------------------------------------------------


def _record_for(state_path: str) -> tuple[dict, str]:
    """The checkpoints.json record that owns a Tinker state path, and the checkpoint's name."""
    for rec in json.loads((TRAIN_DIR / "checkpoints.json").read_text()):
        if rec.get("state_path") == state_path:
            return rec, "final"
        for c in rec.get("checkpoints", []):
            if c.get("state_path") == state_path:
                return rec, c["name"]
    raise KeyError(f"no run in checkpoints.json owns {state_path}")


def _test_row(eval_dir: str, key: str) -> dict:
    return json.loads((RESULTS_DIR / eval_dir / "summary.json").read_text())["models"][key]


def adapter_rows() -> list[dict]:
    """Every exported student adapter joined to its training record and its pre-registered test row."""
    rows = []
    for folder, eval_dir, key, what in ADAPTERS:
        manifest = json.loads((TRAIN_DIR / f"adapter_manifest_{folder}.json").read_text())
        rec, checkpoint = _record_for(manifest["state_path"])
        row = _test_row(eval_dir, key)
        label = row["label"]
        if rec["name"] not in label and rec["run_id"] not in label:
            raise ValueError(f"{folder}: test row {label!r} does not belong to run {rec['name']}")
        if checkpoint != "final" and not label.endswith(checkpoint):
            raise ValueError(f"{folder}: test row {label!r} is not checkpoint {checkpoint}")
        rows.append({
            "folder": folder, "model": manifest["model"], "what": what, "run": rec["name"], "checkpoint": checkpoint,
            "kind": rec["kind"], "learning_rate": rec["learning_rate"], "lora_rank": rec["lora_rank"],
            "steps": rec.get("steps"), "epochs": rec.get("epochs"), "batch_size": rec.get("batch_size"),
            "tasks_per_step": rec.get("tasks_per_step"), "group_size": rec.get("group_size"),
            "max_tokens": rec.get("max_tokens") or rec.get("max_length"), "seed": rec.get("seed"),
            "pass": row["pass_all_samples"], "leak": row["leak_all_samples"], "n": row["samples"], "eval_dir": eval_dir,
            "bytes": sum(f["bytes"] for f in manifest["files"].values()),
        })
    return rows


def _pct(x: dict) -> str:
    return f"{round(100 * x['rate'])}%"


def _ci(x: dict) -> str:
    return f"[{round(100 * x['lo'])}–{round(100 * x['hi'])}]"


def _recipe(r: dict) -> str:
    if r["kind"] == "sft":
        return f"SFT, {r['epochs']} epochs ({r['steps']} steps), batch {r['batch_size']}"
    if r["kind"] == "distil":
        return f"distillation, {r['steps']} steps × {r['tasks_per_step']} tasks × {r['group_size']} rollouts"
    return f"GRPO, {r['steps']} steps × {r['tasks_per_step']} tasks × {r['group_size']} rollouts, seed {r['seed']}"


def adapter_table(rows: list[dict]) -> str:
    lines = ["| Folder | Base model | What | Test pass | Test leak | Size |", "|---|---|---|---|---|---|"]
    for model, eval_dir, key in BASE_ROWS:
        b = _test_row(eval_dir, key)
        lines.append(f"| *(none: the base model)* | `{model}` | untrained | {_pct(b['pass_all_samples'])} "
                     f"{_ci(b['pass_all_samples'])} | {_pct(b['leak_all_samples'])} | |")
    for r in rows:
        lines.append(f"| `{r['folder']}` | `{r['model']}` | {r['what']} | {_pct(r['pass'])} {_ci(r['pass'])} | "
                     f"{_pct(r['leak'])} | {r['bytes'] / 1e6:,.0f} MB |")
    return "\n".join(lines)


def training_table(rows: list[dict]) -> str:
    lines = ["| Folder | Tinker run | Checkpoint | Recipe | Learning rate | Rank | Max tokens | Test evaluation |",
             "|---|---|---|---|---|---|---|---|"]
    for r in rows:
        lines.append(f"| `{r['folder']}` | `{r['run']}` | {r['checkpoint']} | {_recipe(r)} | {r['learning_rate']:.2g} | "
                     f"{r['lora_rank']} | {r['max_tokens']:,} | `results/{r['eval_dir']}/` |")
    return "\n".join(lines)


def judge_line() -> str:
    manifest = json.loads((TRAIN_DIR / f"adapter_manifest_{JUDGE_FOLDER}.json").read_text())
    rec, _ = _record_for(manifest["state_path"])
    j = json.loads((RESULTS_DIR / "judge" / "summary.json").read_text())[JUDGE_KEY]
    if rec["run_id"] not in JUDGE_KEY:
        raise ValueError(f"judge summary key {JUDGE_KEY!r} is not run {rec['run_id']}")
    stats = json.loads((RESULTS_DIR / "judge" / "data_stats.json").read_text())
    size = sum(f["bytes"] for f in manifest["files"].values()) / 1e6
    return (f"`{JUDGE_FOLDER}` ({size:,.0f} MB, base `{manifest['model']}`) is a judge, not a policy writer: given a task and a "
            f"candidate policy it predicts the harness verdict (pass, leak, block or error). SFT on {stats['train']['examples']:,} "
            f"harness-labelled candidates, {rec['epochs']} epochs, learning rate {rec['learning_rate']:.2g}, rank {rec['lora_rank']}. "
            f"On {j['n']} held-out candidates: κ {j['kappa_4class']:.2f} against the harness over the four classes, "
            f"leak recall {_pct(j['leak_recall'])}, leak precision {_pct(j['leak_precision'])}, "
            f"and {_pct(j['unsafe_as_pass'])} of leaks called a pass.")


# --- cards and staging ---------------------------------------------------------------------------


def render_cards() -> tuple[str, str]:
    """(dataset card, adapters card) with every placeholder filled from results/."""
    rows = adapter_rows()
    fills = {
        "<!-- split-table -->": split_table(task_rows()),
        "<!-- adapter-table -->": adapter_table(rows),
        "<!-- training-table -->": training_table(rows),
        "<!-- judge-line -->": judge_line(),
    }
    out = []
    for name in ("dataset.md", "adapters.md"):
        text = (CARDS_DIR / name).read_text()
        for marker, filled in fills.items():
            text = text.replace(marker, filled)
        if "<!--" in text:
            raise ValueError(f"{name}: unfilled placeholder")
        out.append(text)
    return out[0], out[1]


def stage_dataset(staging: Path = STAGING_DIR) -> dict[str, int]:
    """Write the dataset tree; returns the row count per split."""
    if staging.exists():
        shutil.rmtree(staging)
    (staging / "data").mkdir(parents=True)
    rows = task_rows()
    counts: dict[str, int] = {}
    for name in ("train", "dev", "test"):
        part = [r for r in rows if r["split"] == name]
        counts[name] = len(part)
        with (staging / "data" / f"{name}.jsonl").open("w") as f:
            for r in part:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
    shutil.copy(split_mod.SPLIT_PATH, staging / "split.json")
    shutil.copytree(TASKS_DIR, staging / "tasks", ignore=shutil.ignore_patterns(".DS_Store", "__pycache__", "split.json"))
    dataset_card, _ = render_cards()
    (staging / "README.md").write_text(dataset_card)
    return counts


@app.command()
def build(staging: Path = typer.Option(STAGING_DIR, help="Where to write the dataset tree.")) -> None:
    """Stage the dataset and write both cards; no network."""
    counts = stage_dataset(staging)
    _, adapters_card = render_cards()
    (ADAPTERS_DIR / "README.md").write_text(adapters_card)
    n_files = sum(1 for p in staging.rglob("*") if p.is_file())
    typer.echo(f"dataset: {counts} rows, {n_files} files under {staging.relative_to(ROOT)}")
    typer.echo(f"adapters card: {ADAPTERS_DIR.relative_to(ROOT)}/README.md ({len(adapter_rows())} student adapters + judge)")


@app.command()
def cards() -> None:
    """Render both cards and push only the two README files (no weights, no task files)."""
    from huggingface_hub import HfApi

    dataset_card, adapters_card = render_cards()
    api = HfApi(token=load_hf_token())
    for repo_id, repo_type, text in ((DATASET_REPO, "dataset", dataset_card), (ADAPTERS_REPO, "model", adapters_card)):
        info = api.upload_file(path_or_fileobj=text.encode(), path_in_repo="README.md", repo_id=repo_id, repo_type=repo_type,
                               commit_message="Update the card from docs/hf/ and results/")
        typer.echo(f"{repo_type} card: {info.commit_url}")


@app.command()
def upload(dataset: bool = typer.Option(True, help="Push the task set."),
           adapters: bool = typer.Option(True, help="Push the adapters."),
           staging: Path = typer.Option(STAGING_DIR)) -> None:
    """Build, then push the dataset and the adapters to Hugging Face."""
    from huggingface_hub import HfApi

    build(staging)
    api = HfApi(token=load_hf_token())
    user = api.whoami()["name"]
    if user != HF_USER:
        raise typer.BadParameter(f"token belongs to {user}, not {HF_USER}")
    if dataset:
        api.create_repo(DATASET_REPO, repo_type="dataset", exist_ok=True)
        info = api.upload_folder(repo_id=DATASET_REPO, repo_type="dataset", folder_path=staging,
                                 commit_message="Task set, split and card from the RLS-Bench repo",
                                 ignore_patterns=[".DS_Store"])
        typer.echo(f"dataset: {info.commit_url}")
    if adapters:
        missing = [f for f, *_ in ADAPTERS + [(JUDGE_FOLDER,)] if not (ADAPTERS_DIR / f / "adapter_model.safetensors").exists()]
        if missing:
            raise typer.BadParameter(f"adapters not exported locally: {', '.join(missing)} (run train/export.py)")
        total = sum((ADAPTERS_DIR / f / "adapter_model.safetensors").stat().st_size for f, *_ in ADAPTERS + [(JUDGE_FOLDER,)])
        typer.echo(f"adapters: {len(ADAPTERS) + 1} folders, {total / 1e9:.2f} GB of weights; resumable upload")
        api.create_repo(ADAPTERS_REPO, repo_type="model", exist_ok=True)
        api.upload_large_folder(ADAPTERS_REPO, ADAPTERS_DIR, repo_type="model",
                                allow_patterns=["*/adapter_config.json", "*/adapter_model.safetensors", "*/manifest.json", "README.md"],
                                print_report_every=120)
        typer.echo(f"adapters: https://huggingface.co/{ADAPTERS_REPO}")


if __name__ == "__main__":
    app()
