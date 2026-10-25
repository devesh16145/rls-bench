"""Plot a GRPO run as a standalone SVG: train reward per step, and dev pass / leak rates at each eval.

Two panels, each with its own y-axis (reward and rates have different scales). Dev step 0 is the SFT
parent's dev eval from results/tinker_eval/. Hand-written SVG, no plotting dependency.
"""

from __future__ import annotations

import json
from pathlib import Path

import typer

from harness.db import ROOT
from train.plot_loss import GRID, INK, MUTED, SURFACE
from train.sft_tinker import CHECKPOINTS_PATH, RESULTS_DIR
from train import eval_tinker

W, PANEL_H, GAP = 760, 260, 40
LEFT, RIGHT, TOP = 64, 124, 52
BLUE, BLUE_LIGHT, ORANGE = "#2a78d6", "#86b6ef", "#eb6834"  # categorical slots 1-2 (validated), blue step 250

app = typer.Typer(add_completion=False)


def all_sample_rates(label: str) -> tuple[float, float]:
    records = [json.loads(line) for line in eval_tinker.results_path(label).read_text().splitlines()]
    n = len(records)
    return sum(r["result"]["passed"] for r in records) / n, sum(bool(r["result"]["leak"]) for r in records) / n


def rolling(values: list[float], window: int) -> list[float]:
    return [sum(values[max(0, i - window + 1):i + 1]) / len(values[max(0, i - window + 1):i + 1]) for i in range(len(values))]


def render(steps: list[dict], dev: list[tuple[int, float, float]], best_step: int | None, title: str) -> str:
    x_max = max([s["step"] + 1 for s in steps] + [d[0] for d in dev]) or 1
    pw = W - LEFT - RIGHT

    def x(s: float) -> float:
        return LEFT + s / x_max * pw

    H = TOP + 2 * PANEL_H + GAP + 48
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" font-family="system-ui, sans-serif" font-size="12">',
           f'<rect width="{W}" height="{H}" fill="{SURFACE}"/>',
           f'<text x="{LEFT}" y="24" font-size="15" font-weight="600" fill="{INK}">{title}</text>']

    def panel(top: float, y_lo: float, y_hi: float, ticks: list[float], fmt, label: str) -> callable:
        ph = PANEL_H - 36

        def y(v: float) -> float:
            return top + (1 - (v - y_lo) / (y_hi - y_lo)) * ph

        for v in ticks:
            out.append(f'<line x1="{LEFT}" x2="{W - RIGHT}" y1="{y(v):.1f}" y2="{y(v):.1f}" stroke="{GRID}"/>')
            out.append(f'<text x="{LEFT - 8}" y="{y(v) + 4:.1f}" text-anchor="end" fill="{MUTED}">{fmt(v)}</text>')
        out.append(f'<text x="{LEFT}" y="{top - 12}" font-weight="600" fill="{INK}">{label}</text>')
        if best_step is not None:
            out.append(f'<line x1="{x(best_step):.1f}" x2="{x(best_step):.1f}" y1="{top}" y2="{top + ph}" stroke="{MUTED}" stroke-dasharray="3 4"/>')
        for s in range(0, x_max + 1, 5):
            out.append(f'<text x="{x(s):.1f}" y="{top + ph + 16}" text-anchor="middle" fill="{MUTED}">{s}</text>')
        return y

    # Panel 1: train reward.
    rewards = [s["mean_reward"] for s in steps]
    lo, hi = min(-0.5, min(rewards)), max(1.0, max(rewards))
    y1 = panel(TOP + 10, lo, hi, [-0.5, 0, 0.5, 1.0], lambda v: f"{v:+.1f}" if v else "0",
               "Train mean reward per step")
    raw = " ".join(f"{x(s['step'] + 1):.1f},{y1(s['mean_reward']):.1f}" for s in steps)
    smooth = rolling(rewards, 5)
    out.append(f'<polyline points="{raw}" fill="none" stroke="{BLUE_LIGHT}" stroke-width="1.5"/>')
    out.append('<polyline points="' + " ".join(f"{x(s['step'] + 1):.1f},{y1(v):.1f}" for s, v in zip(steps, smooth))
               + f'" fill="none" stroke="{BLUE}" stroke-width="2"/>')
    for s in steps:
        out.append(f'<circle cx="{x(s["step"] + 1):.1f}" cy="{y1(s["mean_reward"]):.1f}" r="6" fill="transparent">'
                   f'<title>step {s["step"] + 1}: reward {s["mean_reward"]:+.3f}, pass {s["pass_rate"]:.0%}, leak {s["leak_rate"]:.0%}</title></circle>')
    out.append(f'<text x="{W - RIGHT + 8}" y="{y1(smooth[-1]) + 4:.1f}" fill="{INK}">5-step mean</text>')
    out.append(f'<text x="{W - RIGHT + 8}" y="{y1(smooth[-1]) + 18:.1f}" fill="{MUTED}">light: per step</text>')

    # Panel 2: dev rates.
    top2 = TOP + 10 + PANEL_H + GAP
    y2 = panel(top2, 0.0, max(0.5, max(max(d[1], d[2]) for d in dev) + 0.05), [0, 0.1, 0.2, 0.3, 0.4, 0.5],
               lambda v: f"{v:.0%}", "Dev (11 tasks × 6 samples): pass and leak rate, step 0 = SFT")
    for idx, (color, name) in ((1, (BLUE, "pass")), (2, (ORANGE, "leak"))):
        pts = " ".join(f"{x(d[0]):.1f},{y2(d[idx]):.1f}" for d in dev)
        out.append(f'<polyline points="{pts}" fill="none" stroke="{color}" stroke-width="2"/>')
        for d in dev:
            out.append(f'<circle cx="{x(d[0]):.1f}" cy="{y2(d[idx]):.1f}" r="4" fill="{color}" stroke="{SURFACE}" stroke-width="2">'
                       f'<title>step {d[0]}: {name} {d[idx]:.0%}</title></circle>')
        out.append(f'<text x="{W - RIGHT + 8}" y="{y2(dev[-1][idx]) + 4:.1f}" fill="{INK}">{name} {dev[-1][idx]:.0%}</text>')
    if best_step is not None:
        out.append(f'<text x="{x(best_step) + 4:.1f}" y="{top2 + 12}" fill="{MUTED}">best dev: step {best_step}</text>')
    out.append(f'<text x="{LEFT + pw / 2}" y="{H - 10}" text-anchor="middle" fill="{INK}">optimizer step</text>')
    out.append("</svg>")
    return "\n".join(out) + "\n"


@app.command()
def main(run_id: str) -> None:
    ck = next(r for r in json.loads(CHECKPOINTS_PATH.read_text()) if r["run_id"] == run_id)
    steps = [json.loads(line) for line in (ROOT / ck["metrics"]).read_text().splitlines()]
    slug = ck["model"].split("/")[-1]
    dev = [(0, *all_sample_rates(f"{slug}@sft-{ck['parent_run_id']}"))]
    dev += [(e["step"], e["dev_pass_all_samples"], all_sample_rates(e["label"])[1]) for e in ck["dev_evals"]]
    title = f"GRPO from SFT, Nemotron-3.5-Lightning (run {run_id}, leak penalty {ck['leak_penalty']})"
    path = RESULTS_DIR / f"rl_{slug}_{run_id}.svg"
    path.write_text(render(steps, dev, ck.get("best_dev_step"), title))
    typer.echo(f"wrote {path.relative_to(ROOT)}")


if __name__ == "__main__":
    app()
