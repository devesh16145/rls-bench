"""Recompute the training write-up's dev and test tables from stored records (no API calls).

Writes results/train/report.json: dev pass/leak with Wilson intervals per checkpoint, test pass/leak per
model overall and by tier, and paired two-sided sign tests per task on test.
"""

from __future__ import annotations

import json
from math import comb
from typing import Any

import typer

from eval.metrics import _latest, load_task_meta, wilson
from harness import split as splitmod
from train import eval_tinker
from train.sft_tinker import CHECKPOINTS_PATH, RESULTS_DIR
from train.test_eval import TEST_DIR

app = typer.Typer(add_completion=False)


def sign_test(better: int, worse: int) -> float:
    """Two-sided exact sign test; ties are dropped before calling."""
    n = better + worse
    if n == 0:
        return 1.0
    return min(1.0, 2 * sum(comb(n, i) for i in range(min(better, worse) + 1)) / 2 ** n)


def rates(records: list[dict[str, Any]]) -> dict[str, Any]:
    greedy = [r for r in records if r["temperature"] == 0.0]
    count = lambda field, rs: sum(bool(r["result"][field]) for r in rs)  # noqa: E731
    return {"samples": len(records), "pass": wilson(count("passed", records), len(records)),
            "leak": wilson(count("leak", records), len(records)),
            "apply_error": wilson(count("apply_error", records), len(records)),
            "greedy_pass": f"{count('passed', greedy)}/{len(greedy)}", "greedy_leak": f"{count('leak', greedy)}/{len(greedy)}",
            "mean_completion_tokens": round(sum(r["usage"]["completion_tokens"] for r in records) / len(records))}


def load(path) -> list[dict[str, Any]]:
    return list(_latest(json.loads(line) for line in path.read_text().splitlines()).values())


@app.command()
def main(sft_run: str = "20261025T125454Z", rl_run: str = "20261025T133618Z") -> None:
    meta = load_task_meta()
    ck = {r["run_id"]: r for r in json.loads(CHECKPOINTS_PATH.read_text())}
    slug = ck[sft_run]["model"].split("/")[-1]
    dev_labels = {"base": f"{slug}@base", "sft": f"{slug}@sft-{sft_run}"}
    dev_labels |= {f"rl step {e['step']}": e["label"] for e in ck[rl_run]["dev_evals"]}
    dev = {name: rates(load(eval_tinker.results_path(label))) for name, label in dev_labels.items()}

    test_ids = sorted(splitmod.load()["test"])
    lock = json.loads((TEST_DIR / "LOCK.json").read_text())
    test_records = {m["name"]: load(eval_tinker.results_path(m["label"], TEST_DIR)) for m in lock["models"]}
    test = {}
    per_task: dict[str, dict[str, dict[str, int]]] = {}
    for name, recs in test_records.items():
        test[name] = rates(recs)
        test[name]["by_tier"] = {}
        for tier in sorted({meta[t].tier for t in test_ids}):
            test[name]["by_tier"][str(tier)] = {k: v for k, v in rates([r for r in recs if meta[r["task_id"]].tier == tier]).items()
                                                if k in ("samples", "pass", "leak")}
        per_task[name] = {t: {"passed": sum(r["result"]["passed"] for r in recs if r["task_id"] == t),
                              "leaked": sum(bool(r["result"]["leak"]) for r in recs if r["task_id"] == t)} for t in test_ids}
    paired = {}
    for a, b in (("sft", "base"), ("sft+rl", "sft"), ("sft+rl", "base")):
        pb = sum(per_task[a][t]["passed"] > per_task[b][t]["passed"] for t in test_ids)
        pw = sum(per_task[a][t]["passed"] < per_task[b][t]["passed"] for t in test_ids)
        lb = sum(per_task[a][t]["leaked"] < per_task[b][t]["leaked"] for t in test_ids)
        lw = sum(per_task[a][t]["leaked"] > per_task[b][t]["leaked"] for t in test_ids)
        paired[f"{a} vs {b}"] = {"pass_better": pb, "pass_worse": pw, "pass_p": round(sign_test(pb, pw), 2),
                                 "leak_lower": lb, "leak_higher": lw, "leak_p": round(sign_test(lb, lw), 2)}
    out = {"dev": dev, "test": test, "test_paired_by_task": paired, "test_per_task": per_task,
           "test_lock": {k: lock[k] for k in ("created", "git_commit")}}
    path = RESULTS_DIR / "report.json"
    path.write_text(json.dumps(out, indent=2) + "\n")
    typer.echo(f"wrote {path}")


if __name__ == "__main__":
    app()
