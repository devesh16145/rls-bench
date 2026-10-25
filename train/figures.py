"""Every figure in the write-up, regenerated from files under results/ (no API calls).

`python -m train.figures all` writes results/figures/<name>.png and .svg. Each figure function returns
the path it wrote, or None when its data is not there yet.
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import typer  # noqa: E402

from harness.db import ROOT  # noqa: E402

FIG_DIR = ROOT / "results" / "figures"
RESULTS = ROOT / "results"
# Categorical slots 1-4 of a validated palette (adjacent-pair colour-blind separation checked), plus neutrals.
BLUE, ORANGE, AQUA, YELLOW = "#2a78d6", "#eb6834", "#1baf7a", "#eda100"
BLUE_LIGHT = "#86b6ef"
INK, MUTED, GRID = "#1f2328", "#6e7781", "#e6e8eb"
SERIES = {"base": MUTED, "sft": BLUE, "sft+rl": ORANGE, "repair": AQUA, "distil": YELLOW}

app = typer.Typer(add_completion=False)


@app.callback()
def _cli() -> None:
    """Subcommands below."""


plt.rcParams.update({
    "font.family": "sans-serif", "font.size": 10, "axes.edgecolor": GRID, "axes.labelcolor": INK, "axes.titlesize": 11,
    "axes.titleweight": "bold", "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True,
    "grid.color": GRID, "grid.linewidth": 0.8, "xtick.color": MUTED, "ytick.color": MUTED, "legend.frameon": False,
    "figure.dpi": 150, "savefig.bbox": "tight", "figure.constrained_layout.use": True,
})


def _jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()] if path.exists() else []


def _save(fig, name: str) -> Path:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIG_DIR / f"{name}.png")
    fig.savefig(FIG_DIR / f"{name}.svg")
    plt.close(fig)
    return FIG_DIR / f"{name}.png"


def _ci_bar(ax, xs, rows, key, color, label=None, width=0.6, offset=0.0):
    rates = [r[key]["rate"] * 100 for r in rows]
    lo = [r[key]["rate"] * 100 - r[key]["lo"] * 100 for r in rows]
    hi = [r[key]["hi"] * 100 - r[key]["rate"] * 100 for r in rows]
    bars = ax.bar([x + offset for x in xs], rates, width=width, color=color, label=label, zorder=3)
    ax.errorbar([x + offset for x in xs], rates, yerr=[lo, hi], fmt="none", ecolor=INK, elinewidth=1, capsize=3, zorder=4)
    for b, r, h in zip(bars, rates, hi):
        ax.text(b.get_x() + b.get_width() / 2, r + h + 1.5, f"{r:.0f}%", ha="center", va="bottom", fontsize=8, color=INK)


# --- Leaderboard -------------------------------------------------------------------------------------

def pretty_model(stem: str) -> str:
    name = stem.replace("__", "/").replace("@reasoning-off", " (no reasoning)").replace("@effort-medium", " (effort medium)")
    return name.split("/")[-1]


def fig_leaderboard() -> Path | None:
    path = RESULTS / "leaderboard.json"
    if not path.exists():
        return None
    rows = sorted(json.loads(path.read_text())["models"].items(), key=lambda kv: kv[1]["pass_at_1"]["rate"])
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 0.45 * len(rows) + 1.5), sharey=True)
    ys = list(range(len(rows)))
    names = [pretty_model(k) for k, _ in rows]
    for ax, key, color, title in ((a1, "pass_at_1", BLUE, "Greedy pass@1"), (a2, "leak_rate", ORANGE, "Leak rate (greedy)")):
        vals = [v[key]["rate"] * 100 for _, v in rows]
        lo = [v[key]["rate"] * 100 - v[key]["lo"] * 100 for _, v in rows]
        hi = [v[key]["hi"] * 100 - v[key]["rate"] * 100 for _, v in rows]
        ax.barh(ys, vals, color=color, height=0.6, zorder=3)
        ax.errorbar(vals, ys, xerr=[lo, hi], fmt="none", ecolor=INK, elinewidth=1, capsize=3, zorder=4)
        for y, v, h in zip(ys, vals, hi):
            ax.text(v + h + 1.5, y, f"{v:.0f}%", va="center", fontsize=8, color=INK)
        ax.set_title(title)
        ax.set_xlim(0, 110)
        ax.set_xlabel("% of 103 tasks, 95% Wilson interval")
    a1.set_yticks(ys)
    a1.set_yticklabels(names)
    fig.suptitle("RLS-Bench leaderboard: one greedy answer per task, all 103 tasks", x=0.02, ha="left", fontweight="bold")
    return _save(fig, "leaderboard")


def fig_trap_heatmap() -> Path | None:
    path = RESULTS / "leaderboard.json"
    if not path.exists():
        return None
    models = json.loads(path.read_text())["models"]
    def n_of(m, t):
        return m["by_trap"][t]["pass"]["n"] if t in m["by_trap"] else 0

    traps = sorted({t for m in models.values() for t in m["by_trap"]}, key=lambda t: -min(n_of(m, t) for m in models.values()))
    traps = [t for t in traps if all(n_of(m, t) >= 3 for m in models.values())]
    names = sorted(models, key=lambda k: -models[k]["pass_at_1"]["rate"])
    grid = [[models[k]["by_trap"][t]["pass"]["rate"] * 100 for t in traps] for k in names]
    fig, ax = plt.subplots(figsize=(0.42 * len(traps) + 3, 0.45 * len(names) + 1.5))
    im = ax.imshow(grid, cmap="Blues", vmin=0, vmax=100, aspect="auto")
    ax.set_xticks(range(len(traps)))
    ax.set_xticklabels(traps, rotation=60, ha="right", fontsize=8)
    ax.set_yticks(range(len(names)))
    ax.set_yticklabels([pretty_model(k) for k in names], fontsize=8)
    ax.grid(False)
    for i, row in enumerate(grid):
        for j, v in enumerate(row):
            ax.text(j, i, f"{v:.0f}", ha="center", va="center", fontsize=7, color="white" if v > 55 else INK)
    fig.colorbar(im, ax=ax, label="greedy pass rate on tasks with this trap (%)", shrink=0.8)
    ax.set_title("Which trap patterns each model gets right (tasks carrying the trap, n ≥ 3)")
    return _save(fig, "trap_heatmap")


# --- SFT ---------------------------------------------------------------------------------------------

def fig_sft_sweeps() -> list[Path]:
    out = []
    for sweep in sorted((RESULTS / "train").glob("sft_sweep_*.json")):
        s = json.loads(sweep.read_text())
        fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 3.8))
        colors = [BLUE_LIGHT, BLUE, "#104281"]
        for i, run in enumerate(s["runs"]):
            m = _jsonl(RESULTS / "train" / "runs" / run["name"] / "metrics.jsonl")
            a1.plot([x["step"] for x in m if "train_mean_nll" in x], [x["train_mean_nll"] for x in m if "train_mean_nll" in x],
                    color=colors[i % 3], linewidth=1.5, label=f"lr {run['learning_rate']:g}")
            dev = [(x["step"], x["test/nll"]) for x in m if "test/nll" in x]
            a2.plot([d[0] for d in dev], [d[1] for d in dev], color=colors[i % 3], linewidth=2, marker="o", markersize=4,
                    label=f"lr {run['learning_rate']:g} → {run['final_dev_nll']:.3f}")
        a1.set_title("Training loss per answer token")
        a2.set_title("Dev loss (held-out dev tasks)")
        for ax in (a1, a2):
            ax.set_xlabel("step")
            ax.set_ylabel("mean NLL")
            ax.legend(fontsize=8)
        fig.suptitle(f"SFT learning-rate sweep: {s['model'].split('/')[-1]} (best lr {s['best_learning_rate']:g})", x=0.02, ha="left", fontweight="bold")
        out.append(_save(fig, f"sft_sweep_{s['model'].split('/')[-1]}"))
    return out


# --- RL ----------------------------------------------------------------------------------------------

def _rl_runs() -> list[dict[str, Any]]:
    path = RESULTS / "train" / "checkpoints.json"
    return [r for r in json.loads(path.read_text()) if r.get("kind") == "rl" and r.get("framework") == "cookbook"] if path.exists() else []


def _metric(m: dict[str, Any], *keys: str) -> float | None:
    for k in keys:
        if k in m:
            return m[k]
    return None


def fig_rl_health() -> list[Path]:
    out = []
    for run in _rl_runs():
        m = [x for x in _jsonl(ROOT / run["metrics"]) if "step" in x or "progress/batch" in x]
        if not m:
            continue
        steps = [_metric(x, "step", "progress/batch") for x in m]
        panels = [("reward/total", "mean reward", BLUE), ("env/all/pass", "pass rate", BLUE), ("env/all/leak", "leak rate", ORANGE),
                  ("optim/kl_sample_train_v1", "KL(sampler ‖ trainer)", AQUA), ("optim/entropy", "entropy per token", AQUA),
                  ("env/all/ac_tokens_per_turn", "answer tokens", YELLOW)]
        keys = list(m[-1].keys())

        def find(key: str) -> str | None:
            if key in keys:
                return key
            tail = key.split("/")[-1]
            cands = [k for k in keys if k.endswith(tail) and ("all" in k or "/" not in k or k.startswith("optim") or k.startswith("reward"))]
            return cands[0] if cands else None

        fig, axes = plt.subplots(2, 3, figsize=(12, 6))
        for ax, (key, title, color) in zip(axes.flat, panels):
            k = find(key)
            if k is None:
                ax.set_title(f"{title} (not logged)")
                continue
            ys = [x.get(k) for x in m]
            ax.plot([s for s, y in zip(steps, ys) if y is not None], [y for y in ys if y is not None], color=color, linewidth=1.5)
            ax.set_title(title)
            ax.set_xlabel("step")
        fig.suptitle(f"GRPO training health: {run['name']} (lr {run['learning_rate']:g}, {run['tasks_per_step']}×{run['group_size']} rollouts/step)",
                     x=0.02, ha="left", fontweight="bold")
        out.append(_save(fig, f"rl_health_{run['name']}"))
    return out


def _sft_dev_point(run: dict[str, Any]) -> tuple[float, float] | None:
    """The parent SFT model's dev rates (step 0), from its standalone dev eval if it exists."""
    parent = run.get("parent_run_id")
    if not parent:
        return None
    path = RESULTS / "tinker_eval" / f"{run['model'].split('/')[-1]}@sft-{parent}.jsonl"
    if not path.exists():
        return None
    latest: dict[tuple, dict] = {}
    for r in _jsonl(path):
        latest[(r["task_id"], r["temperature"], r["index"])] = r
    rs = list(latest.values())
    return (sum(r["result"]["passed"] for r in rs) / len(rs), sum(bool(r["result"]["leak"]) for r in rs) / len(rs))


def fig_dev_curves() -> list[Path]:
    out = []
    for run in _rl_runs():
        evals = run.get("dev_evals") or []
        if not evals or "dev/pass_all" not in evals[0]:
            continue
        every = run["steps"] // len(evals)  # the loop evaluates at every, 2*every, ..., steps
        xs = [every * (i + 1) for i in range(len(evals))]
        passes = [e["dev/pass_all"] * 100 for e in evals]
        leaks = [e["dev/leak_all"] * 100 for e in evals]
        ref = _sft_dev_point(run)
        if ref:
            xs, passes, leaks = [0] + xs, [ref[0] * 100] + passes, [ref[1] * 100] + leaks
        fig, ax = plt.subplots(figsize=(7, 3.8))
        ax.plot(xs, passes, color=BLUE, marker="o", linewidth=2, label="pass (all 66 dev samples)")
        ax.plot(xs, leaks, color=ORANGE, marker="o", linewidth=2, label="leak (all 66 dev samples)")
        best = run.get("best_dev_eval")
        if best:
            bx = every * ([e["label"] for e in evals].index(best["label"]) + 1)
            ax.axvline(bx, color=MUTED, linestyle=":", linewidth=1)
            at_edge = bx >= 0.8 * max(xs)
            ax.text(bx - 0.5 if at_edge else bx + 0.5, 2, f"best dev: step {bx}", color=MUTED, va="bottom", fontsize=8,
                    ha="right" if at_edge else "left")
        if ref:
            ax.text(0.5, passes[0] + 2, "SFT", color=MUTED, fontsize=8)
        ax.set_xlabel("optimizer step (0 = the SFT model it started from)")
        ax.set_ylabel("% of dev samples")
        ax.set_ylim(0, max(60, max(passes + leaks) + 8))
        ax.legend(fontsize=8, loc="upper left")
        ax.set_title(f"Dev during GRPO: {run['name']}")
        out.append(_save(fig, f"dev_curve_{run['name']}"))
    return out


# --- Test --------------------------------------------------------------------------------------------

def fig_test_bars() -> Path | None:
    path = RESULTS / "test_eval_v2" / "summary.json"
    if not path.exists():
        return None
    s = json.loads(path.read_text())
    names = list(s["models"])
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 4))
    xs = list(range(len(names)))
    _ci_bar(a1, xs, [s["models"][n] for n in names], "pass_all_samples", BLUE)
    _ci_bar(a2, xs, [s["models"][n] for n in names], "leak_all_samples", ORANGE)
    for ax, t in ((a1, "Pass rate, all 120 test samples"), (a2, "Leak rate, all 120 test samples")):
        ax.set_xticks(xs)
        ax.set_xticklabels(names, rotation=15, ha="right")
        ax.set_ylim(0, 100)
        ax.set_ylabel("%")
        ax.set_title(t)
    fig.suptitle("Test split (20 tasks × 6 samples), evaluated once for version 2", x=0.02, ha="left", fontweight="bold")
    return _save(fig, "test_bars")


def fig_test_by_tier() -> Path | None:
    path = RESULTS / "test_eval_v2" / "summary.json"
    if not path.exists():
        return None
    s = json.loads(path.read_text())
    names = list(s["models"])
    tiers = ["1", "2", "3"]
    fig, ax = plt.subplots(figsize=(8, 4))
    w = 0.8 / len(names)
    colors = [MUTED, BLUE, ORANGE, AQUA, YELLOW, "#6250d6"]
    for i, n in enumerate(names):
        vals = [s["models"][n]["by_tier"][t]["pass"]["rate"] * 100 for t in tiers]
        ax.bar([j + i * w for j in range(3)], vals, width=w, color=colors[i % len(colors)], label=n, zorder=3)
    ax.set_xticks([j + w * (len(names) - 1) / 2 for j in range(3)])
    ax.set_xticklabels([f"tier {t}" for t in tiers])
    ax.set_ylabel("pass rate, all samples (%)")
    ax.legend(fontsize=8)
    ax.set_title("Test pass rate by tier")
    return _save(fig, "test_by_tier")


def fig_methods() -> Path | None:
    """SFT vs GRPO vs distillation (and repair) on test: pass and leak over all 120 samples, Qwen rows only."""
    path = RESULTS / "test_eval_v2" / "summary.json"
    if not path.exists():
        return None
    s = json.loads(path.read_text())["models"]
    order = [("base", "base"), ("sft", "SFT"), ("distil", "distillation"), ("sft+rl", "SFT + GRPO"), ("sft+rl-seed1", "SFT + GRPO, seed 1"), ("repair", "repair-trained")]
    rows = [(label, s[k]) for k, label in order if k in s]
    if not rows:
        return None
    fig, ax = plt.subplots(figsize=(8, 4))
    xs = list(range(len(rows)))
    _ci_bar(ax, [x - 0.2 for x in xs], [r for _, r in rows], "pass_all_samples", BLUE, label="pass", width=0.38)
    _ci_bar(ax, [x + 0.2 for x in xs], [r for _, r in rows], "leak_all_samples", ORANGE, label="leak", width=0.38)
    ax.set_xticks(xs)
    ax.set_xticklabels([l for l, _ in rows], rotation=12, ha="right")
    ax.set_ylim(0, 100)
    ax.set_ylabel("% of 120 test samples")
    ax.legend(fontsize=8, loc="upper left")
    ax.set_title("Three ways to train the same 9B model, on the test split")
    return _save(fig, "methods_test")


# --- Repair --------------------------------------------------------------------------------------

def fig_repair() -> Path | None:
    """Pass rate after 1, 2 and 3 tries with harness feedback, per model, on dev (summary files from train/repair_eval.py)."""
    rdir = RESULTS / "repair_eval"
    files = sorted(rdir.glob("*.summary.json")) if rdir.exists() else []
    if not files:
        return None
    rows = []
    for f in files:
        s = json.loads(f.read_text())
        label = f.name.replace(".summary.json", "")
        name = ("base" if "@base" in label else "SFT" if "@sft-" in label else "repair-trained" if "@repair_" in label else "SFT + GRPO")
        rows.append((name, [w["rate"] * 100 for w in s["pass_by_try"]], s["leak_any_try"]["rate"] * 100))
    order = {"base": 0, "SFT": 1, "SFT + GRPO": 2, "repair-trained": 3}
    rows.sort(key=lambda r: order.get(r[0], 9))
    fig, ax = plt.subplots(figsize=(7.5, 4))
    colors = [MUTED, BLUE, ORANGE, AQUA]
    w = 0.8 / len(rows)
    for i, (name, by_try, _) in enumerate(rows):
        xs = [j + i * w for j in range(len(by_try))]
        ax.bar(xs, by_try, width=w, color=colors[i % len(colors)], label=name, zorder=3)
        for x, v in zip(xs, by_try):
            ax.text(x, v + 1, f"{v:.0f}", ha="center", va="bottom", fontsize=7, color=INK)
    ax.set_xticks([j + w * (len(rows) - 1) / 2 for j in range(3)])
    ax.set_xticklabels(["after 1 try", "after 2 tries", "after 3 tries"])
    ax.set_ylabel("% of dev samples passing")
    ax.set_ylim(0, 100)
    ax.legend(fontsize=8, loc="upper left")
    ax.set_title("Repairing with harness feedback (11 dev tasks × 6 samples)")
    return _save(fig, "repair")


# --- Judges and spend --------------------------------------------------------------------------------

def judge_name(stem: str) -> str:
    names = {"zeroshot_Kimi-K2.6": "Kimi K2.6, thinking off", "zeroshot_Kimi-K2.6+kimi_k26": "Kimi K2.6, thinking on",
             "zeroshot_gpt-oss-120b": "gpt-oss-120b, reasoning", "zeroshot_claude-opus-5-5": "Claude Opus 5.5, effort medium"}
    if stem in names:
        return names[stem]
    if stem.startswith("trained_"):
        return "trained " + stem.split("_")[1] + " (LoRA)"
    return stem


def fig_judges() -> Path | None:
    path = RESULTS / "judge" / "summary.json"
    if not path.exists():
        return None
    s = json.loads(path.read_text())
    names = sorted(s, key=lambda k: s[k]["kappa_4class"])
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 0.5 * len(names) + 1.8), sharey=True)
    ys = list(range(len(names)))
    a1.barh(ys, [s[n]["kappa_4class"] for n in names], color=BLUE, height=0.6, zorder=3)
    for y, n in zip(ys, names):
        a1.text(s[n]["kappa_4class"] + 0.01, y, f"{s[n]['kappa_4class']:.2f}", va="center", fontsize=8)
    a1.set_title("Agreement with the harness (Cohen's κ)")
    a1.set_xlim(0, 1)
    rec = [s[n]["leak_recall"]["rate"] * 100 if s[n]["leak_recall"] else 0 for n in names]
    prec = [s[n]["leak_precision"]["rate"] * 100 if s[n]["leak_precision"] else 0 for n in names]
    a2.barh([y + 0.17 for y in ys], rec, color=ORANGE, height=0.32, label="leak recall", zorder=3)
    a2.barh([y - 0.17 for y in ys], prec, color=BLUE_LIGHT, height=0.32, label="leak precision", zorder=3)
    a2.set_xlim(0, 105)
    a2.set_title("Leak recall and precision (%)")
    a2.legend(fontsize=8, loc="lower right")
    a1.set_yticks(ys)
    a1.set_yticklabels([judge_name(n) for n in names], fontsize=8)
    fig.suptitle("Judges on 400 held-out test-task candidates (100 per label)", x=0.02, ha="left", fontweight="bold")
    return _save(fig, "judges")


def fig_spend() -> Path | None:
    path = RESULTS / "train" / "tinker_spend.json"
    if not path.exists():
        return None
    items = json.loads(path.read_text())["items"]
    groups: dict[str, float] = defaultdict(float)
    for k, v in items.items():
        key = ("judge" if "judge" in k else "leaderboard" if "leaderboard" in k else "GRPO" if k.startswith("rl ") or "GRPO" in k
               else "SFT" if k.startswith("sft") else "evals" if "eval" in k else "other")
        groups[key] += v
    fig, ax = plt.subplots(figsize=(6, 3.2))
    names = sorted(groups, key=lambda k: -groups[k])
    ax.barh(range(len(names)), [groups[n] for n in names], color=BLUE, height=0.6, zorder=3)
    for y, n in enumerate(names):
        ax.text(groups[n] + 0.3, y, f"${groups[n]:.2f}", va="center", fontsize=8)
    ax.set_yticks(range(len(names)))
    ax.set_yticklabels(names)
    ax.set_xlabel("USD, estimated from token counts at list prices")
    ax.set_title(f"Tinker spend by stage (total ${sum(groups.values()):.2f})")
    return _save(fig, "spend")


@app.command("all")
def make_all() -> None:
    made = [fig_leaderboard(), fig_trap_heatmap(), *fig_sft_sweeps(), *fig_rl_health(), *fig_dev_curves(), fig_test_bars(),
            fig_test_by_tier(), fig_methods(), fig_repair(), fig_judges(), fig_spend()]
    for p in made:
        if p:
            typer.echo(str(p.relative_to(ROOT)))


if __name__ == "__main__":
    app()
