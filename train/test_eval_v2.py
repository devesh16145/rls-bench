"""Version 2 test-split evaluation: the rows named in docs/preregistration.md, evaluated once.

Rows are given as `name=ref` where `ref` is a base model name, a run_id from results/train/checkpoints.json
(its final sampler), or `run_id#checkpoint-name` (one of the run's saved checkpoints, e.g. the best dev
one). Same protocol and the same guards as the version 1 script: `--estimate` makes no call; a real run
needs `--yes --once`, a clean git tree, and writes results/test_eval_v2/LOCK.json before the first sample;
only the identical evaluation may run again, to finish a crash.
"""

from __future__ import annotations

import datetime as dt
import json
import warnings
from pathlib import Path
from typing import Any

import typer

warnings.filterwarnings("ignore", message=r'Field "model_')

from eval.prompts import build_messages  # noqa: E402
from harness import split as splitmod  # noqa: E402
from harness.db import ROOT  # noqa: E402
from harness.models import Task  # noqa: E402
from train import eval_tinker  # noqa: E402
from train.rl_cookbook import DEFAULT_RENDERERS  # noqa: E402
from train.sft_tinker import CHECKPOINTS_PATH, load_tinker_key, make_renderer  # noqa: E402
from train.test_eval import K, MAX_TOKENS, check_lock, compare, git_state, lock_content  # noqa: E402

TEST_DIR = ROOT / "results" / "test_eval_v2"
LOCK_PATH = TEST_DIR / "LOCK.json"


def set_version(version: int) -> None:
    global TEST_DIR, LOCK_PATH
    TEST_DIR = ROOT / "results" / f"test_eval_v{version}"
    LOCK_PATH = TEST_DIR / "LOCK.json"

app = typer.Typer(add_completion=False)


def resolve(name: str, ref: str) -> dict[str, Any]:
    """A row: base model, a run's final checkpoint, or run_id#checkpoint."""
    if "/" in ref:  # a base model
        return {"name": name, "label": f"{ref.split('/')[-1]}@base", "model": ref, "renderer": DEFAULT_RENDERERS[ref], "model_path": None}
    run_id, _, ckpt = ref.partition("#")
    from train.rl_cookbook import checkpoint_record

    rec = checkpoint_record(run_id)  # a run name or a run_id
    path = rec["sampler_path"]
    if ckpt:
        c = next((c for c in rec.get("checkpoints", []) if c.get("name") == ckpt), None)
        if c is None or not c.get("sampler_path"):
            raise typer.BadParameter(f"run {run_id} has no sampler checkpoint named {ckpt}")
        path = c["sampler_path"]
    slug = rec["model"].split("/")[-1]
    return {"name": name, "label": f"{slug}@{rec['kind']}-{run_id}" + (f"-{ckpt}" if ckpt else ""), "model": rec["model"],
            "renderer": rec["renderer"], "model_path": path}


def parse_rows(rows: str) -> list[dict[str, Any]]:
    out = []
    for item in rows.split(","):
        name, _, ref = item.partition("=")
        if not name or not ref:
            raise typer.BadParameter(f"bad row {item!r}; use name=ref")
        out.append(resolve(name.strip(), ref.strip()))
    return out


@app.command()
def main(
    rows: str = typer.Option(..., help="Comma-separated name=ref rows, e.g. base=Qwen/Qwen3.5-9B,sft=<run_id>,sft+rl=<run_id>#step-30"),
    repair_rows: str = typer.Option("", help="Rows also evaluated with the 3-try repair protocol (same name=ref form)."),
    max_spend: float = typer.Option(2.0, help="Per row (USD)."),
    estimate_only: bool = typer.Option(False, "--estimate"),
    yes: bool = typer.Option(False, "--yes"),
    once: bool = typer.Option(False, "--once"),
    version: int = typer.Option(2, help="Evaluation version: output directory results/test_eval_v<version>."),
) -> None:
    set_version(version)
    models = parse_rows(rows)
    repair_models = parse_rows(repair_rows) if repair_rows else []
    test_ids = sorted(splitmod.load()["test"])
    tasks = [Task.load(next((ROOT / "tasks").glob(f"{tid}-*"))) for tid in test_ids]
    content = lock_content(models, test_ids, K, MAX_TOKENS)
    content["repair_models"] = [{key: m[key] for key in ("name", "label", "model", "renderer", "model_path")} for m in repair_models]
    content["repair_max_turns"] = 3
    total_typ = total_worst = 0.0
    per_row = {}
    for m in models:
        renderer, _ = make_renderer(m["model"], m["renderer"])
        pt = {t.id: renderer.build_generation_prompt(build_messages(t)).length for t in tasks}
        est = eval_tinker.estimate(pt, m["model"], K, MAX_TOKENS)
        per_row[m["name"]] = {"label": m["label"], "typical_usd": round(est["typical_usd"], 3), "worst_usd": round(est["worst_usd"], 3)}
        total_typ += est["typical_usd"]
        total_worst += est["worst_usd"]
    typer.echo(json.dumps({"split": "test", "tasks": len(tasks), "k": K, "max_tokens": MAX_TOKENS, "rows": per_row,
                           "total_typical_usd": round(total_typ, 2), "total_worst_usd": round(total_worst, 2),
                           "lock": "exists (identical; would resume)" if LOCK_PATH.exists() and check_lock(LOCK_PATH, content) else "none"}, indent=2))
    if estimate_only:
        return
    if not (yes and once):
        raise typer.BadParameter("this spends money and uses the test split again: run --estimate first, then pass --yes --once")
    commit, dirty = git_state()
    if dirty:
        raise typer.BadParameter(f"commit tracked changes first: {dirty[:5]}")
    resuming = check_lock(LOCK_PATH, content)
    if not resuming:
        TEST_DIR.mkdir(parents=True, exist_ok=True)
        LOCK_PATH.write_text(json.dumps({**content, "created": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
                                         "git_commit": commit, "version": version}, indent=2) + "\n")
    typer.echo(("resuming" if resuming else "starting") + f" the version {version} test eval at commit {commit[:7]}")
    load_tinker_key()
    import tinker

    service = tinker.ServiceClient()
    for m in models:
        client = (service.create_sampling_client(model_path=m["model_path"]) if m["model_path"]
                  else service.create_sampling_client(base_model=m["model"]))
        renderer, _ = make_renderer(m["model"], m["renderer"])
        out = eval_tinker.sample_and_grade(client, renderer, tasks, label=m["label"], model=m["model"], model_path=m["model_path"],
                                           renderer_name=m["renderer"], k=K, max_tokens=MAX_TOKENS, max_spend=max_spend,
                                           out_dir=TEST_DIR, log=lambda s: None)
        typer.echo(f"{m['name']}: {out['graded']} graded, est ${out['spent_usd']:.3f}, stopped at cap: {out['stopped_at_cap']}")
    repair_summaries = {}
    for m in repair_models:
        from train import repair_eval

        client = (service.create_sampling_client(model_path=m["model_path"]) if m["model_path"]
                  else service.create_sampling_client(base_model=m["model"]))
        renderer, _ = make_renderer(m["model"], m["renderer"])
        label = m["label"] + "@repair3"
        out = repair_eval.repair_sample_and_grade(client, renderer, tasks, label=label, model=m["model"], model_path=m["model_path"],
                                                  renderer_name=m["renderer"], k=K, max_turns=3, max_tokens=MAX_TOKENS,
                                                  max_spend=3 * max_spend, out_dir=TEST_DIR, log=lambda s: None)
        repair_summaries[m["name"]] = {**repair_eval.summarize(label, tasks, out_dir=TEST_DIR), "est_spend_usd": round(out["spent_usd"], 4)}
        typer.echo(f"{m['name']} (3 tries): pass by try {[round(w['rate'], 3) for w in repair_summaries[m['name']]['pass_by_try']]}, est ${out['spent_usd']:.3f}")
    summary = {"git_commit": commit, "version": version, **compare(models, test_ids, TEST_DIR), "repair": repair_summaries}
    (TEST_DIR / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    for name, row in summary["models"].items():
        typer.echo(f"{name:10} pass {row['pass_all_samples']['rate']:.0%} [{row['pass_all_samples']['lo']:.0%}, {row['pass_all_samples']['hi']:.0%}]  "
                   f"leak {row['leak_all_samples']['rate']:.0%}  apply err {row['apply_error_all_samples']['rate']:.0%}  len {row['mean_completion_tokens']:.0f}")


if __name__ == "__main__":
    app()
