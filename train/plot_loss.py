"""Plot per-step training loss from a results/train/*.jsonl metrics file as a standalone SVG.

No plotting dependency: the SVG is written by hand so the figure is reproducible from the repo alone.
"""

from __future__ import annotations

import json
from pathlib import Path

import typer

W, H = 720, 400
LEFT, RIGHT, TOP, BOTTOM = 64, 24, 48, 56
INK, MUTED, GRID, LINE, SURFACE = "#1f2328", "#6e7781", "#e6e8eb", "#2a6fdb", "#ffffff"

app = typer.Typer(add_completion=False)


def render(rows: list[dict], title: str) -> str:
    steps = [r["step"] for r in rows]
    nll = [r["train_mean_nll"] for r in rows]
    x_max = max(steps) or 1
    y_max = max(0.1, round(max(nll) + 0.05, 1))
    pw, ph = W - LEFT - RIGHT, H - TOP - BOTTOM

    def x(s: float) -> float:
        return LEFT + s / x_max * pw

    def y(v: float) -> float:
        return TOP + (1 - v / y_max) * ph

    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" font-family="system-ui, sans-serif" font-size="12">',
           f'<rect width="{W}" height="{H}" fill="{SURFACE}"/>',
           f'<text x="{LEFT}" y="24" font-size="15" font-weight="600" fill="{INK}">{title}</text>']
    ticks = 5
    for i in range(ticks + 1):
        v = y_max * i / ticks
        out.append(f'<line x1="{LEFT}" x2="{W - RIGHT}" y1="{y(v):.1f}" y2="{y(v):.1f}" stroke="{GRID}"/>')
        out.append(f'<text x="{LEFT - 8}" y="{y(v) + 4:.1f}" text-anchor="end" fill="{MUTED}">{v:.2f}</text>')
    # Epoch boundaries and per-epoch mean.
    epochs = sorted({r["epoch"] for r in rows})
    for e in epochs:
        in_e = [r for r in rows if r["epoch"] == e]
        s0, s1 = in_e[0]["step"], in_e[-1]["step"]
        if e:
            out.append(f'<line x1="{x(s0 - 0.5):.1f}" x2="{x(s0 - 0.5):.1f}" y1="{TOP}" y2="{TOP + ph}" stroke="{MUTED}" stroke-dasharray="3 4"/>')
        mean = sum(r["train_mean_nll"] for r in in_e) / len(in_e)
        out.append(f'<text x="{(x(s0) + x(s1)) / 2:.1f}" y="{TOP - 8}" text-anchor="middle" fill="{MUTED}">epoch {e + 1} · mean {mean:.3f}</text>')
    pts = " ".join(f"{x(s):.1f},{y(v):.1f}" for s, v in zip(steps, nll))
    out.append(f'<polyline points="{pts}" fill="none" stroke="{LINE}" stroke-width="2" stroke-linejoin="round"/>')
    for s, v in zip(steps, nll):
        out.append(f'<circle cx="{x(s):.1f}" cy="{y(v):.1f}" r="6" fill="transparent"><title>step {s}: {v:.4f}</title></circle>')
    for s in range(0, x_max + 1, 10):
        out.append(f'<text x="{x(s):.1f}" y="{TOP + ph + 18}" text-anchor="middle" fill="{MUTED}">{s}</text>')
    out.append(f'<text x="{LEFT + pw / 2}" y="{H - 14}" text-anchor="middle" fill="{INK}">step</text>')
    out.append(f'<text x="16" y="{TOP + ph / 2}" text-anchor="middle" fill="{INK}" transform="rotate(-90 16 {TOP + ph / 2})">train mean NLL (per target token)</text>')
    out.append("</svg>")
    return "\n".join(out) + "\n"


@app.command()
def main(metrics: Path, title: str = typer.Option("SFT training loss")) -> None:
    rows = [json.loads(line) for line in metrics.read_text().splitlines() if line.strip()]
    svg_path = metrics.with_suffix(".svg")
    svg_path.write_text(render(rows, title))
    typer.echo(f"wrote {svg_path}")


if __name__ == "__main__":
    app()
