"""The one-time test-split evaluation (spec §8, Phase 5): base, SFT and the best-dev RL checkpoint.

Guards, so the test split is looked at exactly once:
- `--estimate` renders prompts locally and prints the cost; it makes no Tinker call and writes nothing.
- A real run needs `--yes --once`, a clean git tree for tracked files, and writes results/test_eval/LOCK.json
  (models, checkpoint paths, protocol, git commit) before the first sample.
- If the lock exists, only the identical evaluation may run again (to finish a crashed run; recorded
  samples are skipped). Anything else - another checkpoint, another k - is refused.

Same protocol as the baselines and dev evals: fixed prompt, 1 greedy + 5 at temperature 0.7, max 4,096
tokens, reasoning-off renderer. Raw lines go to results/test_eval/<label>.jsonl; summary.json compares them.
"""

from __future__ import annotations

import datetime as dt
import json
import subprocess
import warnings
from pathlib import Path
from typing import Any

import typer

warnings.filterwarnings("ignore", message=r'Field "model_')  # noisy pydantic warnings from tinker

from eval.metrics import _latest, wilson  # noqa: E402
from eval.prompts import build_messages  # noqa: E402
from harness import split as splitmod  # noqa: E402
from harness.db import ROOT  # noqa: E402
from harness.models import Task  # noqa: E402
from train import eval_tinker  # noqa: E402
from train.sft_tinker import CHECKPOINTS_PATH, DEFAULT_MODEL, DEFAULT_RENDERER, load_tinker_key, make_renderer  # noqa: E402

TEST_DIR = ROOT / "results" / "test_eval"
LOCK_PATH = TEST_DIR / "LOCK.json"
DEFAULT_SFT_RUN = "20261025T125454Z"
DEFAULT_RL_RUN = "20261025T133618Z"
K = 5
MAX_TOKENS = 4096

app = typer.Typer(add_completion=False)


def models_to_test(sft_run: str, rl_run: str, rl_step: int | None) -> list[dict[str, Any]]:
    """Base, SFT and RL entries: label, model, renderer and sampler path (None for the base model)."""
    records = json.loads(CHECKPOINTS_PATH.read_text())
    sft = next((r for r in records if r["run_id"] == sft_run and r["kind"] == "sft"), None)
    rl = next((r for r in records if r["run_id"] == rl_run and r["kind"] == "rl"), None)
    if sft is None or rl is None:
        raise typer.BadParameter(f"need an sft record {sft_run} and an rl record {rl_run} in {CHECKPOINTS_PATH.name}")
    if rl["parent_run_id"] != sft_run:
        raise typer.BadParameter(f"rl run {rl_run} starts from {rl['parent_run_id']}, not {sft_run}")
    step = rl["best_dev_step"] if rl_step is None else rl_step
    ev = next((e for e in rl["dev_evals"] if e["step"] == step), None)
    if ev is None:
        raise typer.BadParameter(f"rl run {rl_run} has no saved checkpoint at step {step}")
    slug = DEFAULT_MODEL.split("/")[-1]
    return [
        {"name": "base", "label": f"{slug}@base", "model": DEFAULT_MODEL, "renderer": DEFAULT_RENDERER, "model_path": None},
        {"name": "sft", "label": f"{slug}@sft-{sft_run}", "model": sft["model"], "renderer": sft["renderer"],
         "model_path": sft["sampler_path"]},
        {"name": "sft+rl", "label": f"{slug}@rl-{rl_run}-step{step:04d}", "model": rl["model"], "renderer": rl["renderer"],
         "model_path": ev["sampler_path"]},
    ]


def lock_content(models: list[dict[str, Any]], task_ids: list[str], k: int, max_tokens: int) -> dict[str, Any]:
    """The part of the lock that must match for a rerun to be allowed."""
    return {"models": [{key: m[key] for key in ("name", "label", "model", "renderer", "model_path")} for m in models],
            "tasks": sorted(task_ids), "k": k, "max_tokens": max_tokens}


def check_lock(lock_path: Path, content: dict[str, Any]) -> bool:
    """True if a lock for this exact evaluation exists (resume); False if none exists. Refuses anything else."""
    if not lock_path.exists():
        return False
    existing = json.loads(lock_path.read_text())
    if {key: existing.get(key) for key in content} != content:
        raise typer.BadParameter(f"the test split was already evaluated with a different setup ({lock_path.relative_to(ROOT)}); "
                                 "it is evaluated once")
    return True


def git_state() -> tuple[str, list[str]]:
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
    dirty = subprocess.run(["git", "status", "--porcelain", "--untracked-files=no"], cwd=ROOT, capture_output=True,
                           text=True, check=True).stdout.splitlines()
    return commit, dirty


def compare(models: list[dict[str, Any]], task_ids: list[str], out_dir: Path) -> dict[str, Any]:
    rows, per_task = {}, {tid: {} for tid in task_ids}
    for m in models:
        latest = _latest(json.loads(line) for line in eval_tinker.results_path(m["label"], out_dir).read_text().splitlines())
        rs = [r for (tid, _, _), r in latest.items() if tid in per_task]
        greedy = [r for (_, temp, _), r in latest.items() if temp == 0.0]
        count = lambda field, recs=rs: sum(bool(r["result"][field]) for r in recs)  # noqa: E731
        rows[m["name"]] = {
            "label": m["label"], "samples": len(rs),
            "pass_all_samples": wilson(count("passed"), len(rs)), "leak_all_samples": wilson(count("leak"), len(rs)),
            "apply_error_all_samples": wilson(count("apply_error"), len(rs)),
            "format_error_all_samples": wilson(count("format_error"), len(rs)),
            "pass_at_1": wilson(count("passed", greedy), len(greedy)), "leak_at_1": wilson(count("leak", greedy), len(greedy)),
            "mean_completion_tokens": sum(r["usage"]["completion_tokens"] for r in rs) / len(rs),
            "est_spend_usd": round(sum(r["cost_usd"] for r in rs), 4),
        }
        for tid in task_ids:
            mine = [r for (t, _, _), r in latest.items() if t == tid]
            per_task[tid][m["name"]] = {"passed": sum(r["result"]["passed"] for r in mine),
                                        "leaked": sum(bool(r["result"]["leak"]) for r in mine), "samples": len(mine)}
    return {"models": rows, "per_task": per_task}


@app.command()
def main(
    sft_run: str = typer.Option(DEFAULT_SFT_RUN),
    rl_run: str = typer.Option(DEFAULT_RL_RUN),
    rl_step: int = typer.Option(None, help="RL checkpoint step; default: the run's best dev step."),
    max_spend: float = typer.Option(2.0, help="Per model: stop before a request whose worst case would pass this (USD)."),
    estimate_only: bool = typer.Option(False, "--estimate", help="Print the cost estimate; no Tinker calls, nothing written."),
    yes: bool = typer.Option(False, "--yes", help="Confirm the spend."),
    once: bool = typer.Option(False, "--once", help="Confirm this is the one-time look at the test split."),
) -> None:
    models = models_to_test(sft_run, rl_run, rl_step)
    test_ids = sorted(splitmod.load()["test"])
    tasks = [Task.load(next((ROOT / "tasks").glob(f"{tid}-*"))) for tid in test_ids]
    content = lock_content(models, test_ids, K, MAX_TOKENS)
    renderer, _ = make_renderer(DEFAULT_MODEL, DEFAULT_RENDERER)
    prompt_tokens = {t.id: renderer.build_generation_prompt(build_messages(t)).length for t in tasks}
    est = eval_tinker.estimate(prompt_tokens, DEFAULT_MODEL, K, MAX_TOKENS)
    typer.echo(json.dumps({"split": "test", "tasks": len(tasks), "k": K, "max_tokens": MAX_TOKENS,
                           "models": [{key: m[key] for key in ("name", "label", "model_path")} for m in models],
                           "per_model": est, "total_typical_usd": round(3 * est["typical_usd"], 4),
                           "total_worst_usd": round(3 * est["worst_usd"], 4),
                           "lock": "exists (identical setup; would resume)" if LOCK_PATH.exists() and check_lock(LOCK_PATH, content)
                           else "none (test split not yet evaluated)"}, indent=2))
    if estimate_only:
        return
    if not (yes and once):
        raise typer.BadParameter("this spends money and uses up the test split: run --estimate first, then pass --yes --once")
    commit, dirty = git_state()
    if dirty:
        raise typer.BadParameter(f"commit or stash tracked changes first, so the result maps to one commit: {dirty}")
    resuming = check_lock(LOCK_PATH, content)
    if not resuming:
        TEST_DIR.mkdir(parents=True, exist_ok=True)
        LOCK_PATH.write_text(json.dumps({**content, "created": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
                                         "git_commit": commit}, indent=2) + "\n")
    typer.echo(("resuming" if resuming else "starting") + f" the one-time test eval at commit {commit[:7]}")

    load_tinker_key()
    import tinker

    service = tinker.ServiceClient()
    for m in models:
        client = (service.create_sampling_client(model_path=m["model_path"]) if m["model_path"]
                  else service.create_sampling_client(base_model=m["model"]))
        r, _ = make_renderer(m["model"], m["renderer"])
        out = eval_tinker.sample_and_grade(client, r, tasks, label=m["label"], model=m["model"], model_path=m["model_path"],
                                           renderer_name=m["renderer"], k=K, max_tokens=MAX_TOKENS, max_spend=max_spend,
                                           out_dir=TEST_DIR, log=typer.echo)
        typer.echo(f"{m['name']}: {out['graded']} graded, est spend ${out['spent_usd']:.3f}, stopped at cap: {out['stopped_at_cap']}")
    summary = {"git_commit": commit, **compare(models, test_ids, TEST_DIR)}
    (TEST_DIR / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    for name, row in summary["models"].items():
        typer.echo(f"{name:7} pass {row['pass_all_samples']['rate']:.0%} [{row['pass_all_samples']['lo']:.0%}, "
                   f"{row['pass_all_samples']['hi']:.0%}]  pass@1 {row['pass_at_1']['rate']:.0%}  "
                   f"leak {row['leak_all_samples']['rate']:.0%} [{row['leak_all_samples']['lo']:.0%}, {row['leak_all_samples']['hi']:.0%}]")


if __name__ == "__main__":
    app()
