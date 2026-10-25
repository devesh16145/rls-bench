"""Experiment D: a trained leak judge versus zero-shot LLM judges (spec §8.2).

A judge reads the access rules, the schema and a candidate's SQL (never the tests) and answers one word:
pass, leak, block or error. Labels come from the harness. Training data: harness-graded samples of train
tasks collected under results/; dev-task samples give the dev loss; test-task samples are the judge
evaluation set. Metrics: agreement with the harness (accuracy, Cohen's kappa over the four labels), leak
precision and recall, and which task traps the leaks a judge misses belong to.

Commands: build, train (LoRA SFT of a small model on the judge data), zero-shot (Kimi / gpt-oss on Tinker,
Opus via the Anthropic API), evaluate (metrics for every judge file under results/judge/).
"""

from __future__ import annotations

import datetime as dt
import glob
import json
import random
import re
import warnings
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import typer

warnings.filterwarnings("ignore", message=r'Field "model_')

from eval.metrics import load_task_meta, wilson  # noqa: E402
from harness import split as splitmod  # noqa: E402
from harness.db import ROOT  # noqa: E402
from harness.models import Task  # noqa: E402
from harness.sqlparse import extract_sql_block  # noqa: E402
from train.build_sft import normalise_sql  # noqa: E402
from train.prices import ANTHROPIC_PRICES, price  # noqa: E402
from train.sft_tinker import CHECKPOINTS_PATH, load_tinker_key, make_renderer  # noqa: E402

DATA_DIR = ROOT / "data"
JUDGE_DIR = ROOT / "results" / "judge"
LABELS = ("pass", "leak", "block", "error")
SYSTEM = (
    "You are a database security reviewer for a Supabase/Postgres application. You are given the access rules, "
    "the schema, and a candidate set of Row Level Security statements written to implement the rules. Decide how "
    "the candidate would behave if applied. Answer with exactly one word:\n"
    "pass - every rule is implemented correctly;\n"
    "leak - some user could read, insert, change or delete data the rules forbid;\n"
    "block - no leak, but some access the rules allow is denied, or a rule is implemented wrongly;\n"
    "error - the SQL would fail to apply, or there is no SQL."
)
DEFAULT_JUDGE_MODEL = "Qwen/Qwen3-8B"
DEFAULT_JUDGE_RENDERER = "qwen3_disable_thinking"
ZERO_SHOT = {"moonshotai/Kimi-K2.6": "kimi_k26_disable_thinking", "openai/gpt-oss-120b": "gpt_oss_medium_reasoning"}
SOURCE_GLOBS = ("results/baselines/*.jsonl", "results/tinker_eval/*.jsonl", "results/test_eval/*.jsonl",
                "results/train/*rollouts*.jsonl", "results/train/rl_filter*.jsonl")

app = typer.Typer(add_completion=False)


@app.callback()
def _cli() -> None:
    """Subcommands below."""


def label_of(result: dict[str, Any]) -> str:
    if result.get("passed"):
        return "pass"
    if result.get("leak"):
        return "leak"
    if result.get("apply_error") or result.get("format_error"):
        return "error"
    return "block"


def candidate_text(completion: str) -> str:
    try:
        return extract_sql_block(completion).strip()
    except Exception:
        return "(no SQL block in the answer)\n" + completion.strip()[:1500]


def judge_messages(task: Task, candidate: str) -> list[dict[str, str]]:
    user = ("## Schema\n\n```sql\n" + task.schema_sql.strip() + "\n```\n\n## Access rules\n\n" + task.requirement.strip()
            + "\n\n## Candidate SQL\n\n```sql\n" + candidate + "\n```\n\nAnswer with one word: pass, leak, block or error.")
    return [{"role": "system", "content": SYSTEM}, {"role": "user", "content": user}]


def collect() -> dict[str, list[dict[str, Any]]]:
    """Every harness-graded sample under results/, deduplicated by (task, normalised SQL), grouped by split."""
    split = splitmod.load()
    of = {t: s for s in ("train", "dev", "test") for t in split[s]}
    seen: set[tuple[str, str]] = set()
    out: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for pattern in SOURCE_GLOBS:
        for path in sorted(glob.glob(str(ROOT / pattern))):
            for line in open(path):
                r = json.loads(line)
                res = r.get("result")
                if not res or "completion" not in r:
                    continue
                text = candidate_text(r["completion"])
                key = (r["task_id"], normalise_sql(text) if not text.startswith("(no SQL") else text[:200])
                if key in seen:
                    continue
                seen.add(key)
                out[of[r["task_id"]]].append({"task_id": r["task_id"], "label": label_of(res), "candidate": text,
                                              "source": Path(path).name})
    return out


def balance(rows: list[dict[str, Any]], per_label: int, seed: int) -> list[dict[str, Any]]:
    rng = random.Random(seed)
    by = defaultdict(list)
    for r in rows:
        by[r["label"]].append(r)
    kept = []
    for lab in LABELS:
        rs = by[lab]
        rng.shuffle(rs)
        kept += rs[:per_label]
    rng.shuffle(kept)
    return kept


def _tasks() -> dict[str, Task]:
    return {p.name.split("-")[0]: Task.load(p) for p in sorted((ROOT / "tasks").glob("T*")) if (p / "task.yaml").exists()}


@app.command()
def build(per_label_train: int = typer.Option(600), per_label_dev: int = typer.Option(40), per_label_test: int = typer.Option(100),
          seed: int = typer.Option(0)) -> None:
    """Write data/judge_{train,dev,test}.jsonl (chat format, one-word assistant answer) and a stats file."""
    tasks = _tasks()
    groups = collect()
    stats = {}
    for name, per in (("train", per_label_train), ("dev", per_label_dev), ("test", per_label_test)):
        rows = balance(groups[name], per, seed)
        with (DATA_DIR / f"judge_{name}.jsonl").open("w") as f:
            for r in rows:
                f.write(json.dumps({"task_id": r["task_id"], "label": r["label"], "source": r["source"],
                                    "messages": judge_messages(tasks[r["task_id"]], r["candidate"]) + [{"role": "assistant", "content": r["label"]}]}) + "\n")
        stats[name] = {"available": dict(Counter(r["label"] for r in groups[name])), "kept": dict(Counter(r["label"] for r in rows)), "examples": len(rows)}
    JUDGE_DIR.mkdir(parents=True, exist_ok=True)
    (JUDGE_DIR / "data_stats.json").write_text(json.dumps(stats, indent=2) + "\n")
    typer.echo(json.dumps(stats, indent=2))


@app.command()
def train(model: str = typer.Option(DEFAULT_JUDGE_MODEL), renderer_name: str = typer.Option(DEFAULT_JUDGE_RENDERER, "--renderer"),
          learning_rate: float = typer.Option(None), epochs: int = typer.Option(2), batch_size: int = typer.Option(16),
          max_length: int = typer.Option(4096), max_spend: float = typer.Option(10.0),
          dry_run: bool = typer.Option(False, "--dry-run"), yes: bool = typer.Option(False, "--yes")) -> None:
    """LoRA SFT of the judge on data/judge_train.jsonl with data/judge_dev.jsonl as the dev loss."""
    from train import sft_cookbook
    from train.rl_cookbook import default_lr

    learning_rate = learning_rate or default_lr(model)
    train_path, dev_path = DATA_DIR / "judge_train.jsonl", DATA_DIR / "judge_dev.jsonl"
    rows, dev_rows = sft_cookbook.load_sets(train_path, dev_path)
    renderer, _ = make_renderer(model, renderer_name)
    _, st = sft_cookbook.build_datums(rows, renderer, max_length)
    _, sd = sft_cookbook.build_datums(dev_rows, renderer, max_length)
    steps = (len(rows) // batch_size) * epochs
    p = price(model)
    usd = (st["tokens"] * epochs * p["train"] + (steps // 10 + 2) * sd["tokens"] * p["prefill"]) / 1e6
    typer.echo(json.dumps({"model": model, "learning_rate": learning_rate, "epochs": epochs, "steps": steps, "train": st, "dev": sd, "usd": round(usd, 2)}, indent=2))
    if dry_run:
        return
    if not yes:
        raise typer.BadParameter("this spends money: run with --dry-run first, then pass --yes")
    if usd > max_spend:
        raise typer.BadParameter(f"estimated ${usd:.2f} exceeds --max-spend ${max_spend}")
    load_tinker_key()
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    sft_cookbook.run_one(model, renderer_name, learning_rate, epochs=epochs, batch_size=batch_size, max_length=max_length,
                         lora_rank=32, eval_every=10, name=f"judge_{model.split('/')[-1]}_{stamp}", train_path=train_path,
                         dev_path=dev_path, recipe="rls_bench_judge", log=typer.echo)


def parse_label(text: str) -> str | None:
    """The judge's verdict: the last label word in the answer (reasoning judges put the verdict last)."""
    found = [w for w in re.findall(r"[a-z]+", text.lower()) if w in LABELS]
    return found[-1] if found else None


def _write_judgements(name: str, rows: list[dict[str, Any]], outputs: list[str], cost: float) -> Path:
    JUDGE_DIR.mkdir(parents=True, exist_ok=True)
    path = JUDGE_DIR / f"{name}.jsonl"
    with path.open("w") as f:
        for r, out in zip(rows, outputs):
            f.write(json.dumps({"judge": name, "task_id": r["task_id"], "label": r["label"], "source": r["source"],
                                "output": out, "predicted": parse_label(out)}) + "\n")
    (JUDGE_DIR / f"{name}.cost.json").write_text(json.dumps({"judge": name, "est_spend_usd": round(cost, 4), "n": len(rows)}) + "\n")
    return path


def _test_rows() -> list[dict[str, Any]]:
    return [json.loads(line) for line in (DATA_DIR / "judge_test.jsonl").read_text().splitlines()]


def _tinker_judge(model: str, renderer_name: str, model_path: str | None, rows: list[dict[str, Any]], name: str,
                  max_tokens: int, log) -> None:
    import tinker

    service = tinker.ServiceClient()
    client = service.create_sampling_client(model_path=model_path) if model_path else service.create_sampling_client(base_model=model)
    renderer, _ = make_renderer(model, renderer_name)
    params = tinker.SamplingParams(max_tokens=max_tokens, temperature=0.0, stop=renderer.get_stop_sequences())
    prompts = [renderer.build_generation_prompt(r["messages"][:-1]) for r in rows]
    futures = [client.sample(p, num_samples=1, sampling_params=params) for p in prompts]
    outputs, cost = [], 0.0
    p = price(model)
    from tinker_cookbook.renderers import get_text_content

    for prompt, fut in zip(prompts, futures):
        seq = fut.result().sequences[0]
        message, _ = renderer.parse_response(seq.tokens)
        outputs.append(get_text_content(message))
        cost += (prompt.length * p["prefill"] + len(seq.tokens) * p["sample"]) / 1e6
    path = _write_judgements(name, rows, outputs, cost)
    log(f"{name}: {len(rows)} judgements, est ${cost:.3f}, {path.relative_to(ROOT)}")


@app.command("zero-shot")
def zero_shot(models: str = typer.Option(",".join(ZERO_SHOT)), opus: bool = typer.Option(True, "--opus/--no-opus"),
              max_tokens: int = typer.Option(32), max_spend: float = typer.Option(10.0), yes: bool = typer.Option(False, "--yes")) -> None:
    """Zero-shot judges on the judge test set: Tinker base models (reasoning off) and Opus via the Anthropic API."""
    rows = _test_rows()
    renderer, _ = make_renderer(DEFAULT_JUDGE_MODEL, DEFAULT_JUDGE_RENDERER)
    tokens = sum(renderer.build_generation_prompt(r["messages"][:-1]).length for r in rows)
    est = {m: round((tokens * price(m.split(":")[0])["prefill"] + len(rows) * max_tokens * price(m.split(":")[0])["sample"]) / 1e6, 3) for m in models.split(",") if m}
    if opus:
        pr = ANTHROPIC_PRICES["claude-opus-5-5"]
        est["claude-opus-5-5"] = round((tokens * pr["input"] + len(rows) * 1500 * pr["output"]) / 1e6, 3)
    typer.echo(json.dumps({"judgements": len(rows), "prompt_tokens": tokens, "estimate_usd": est}, indent=2))
    if not yes:
        raise typer.BadParameter("this spends money: check the estimate, then pass --yes")
    if sum(v for k, v in est.items() if k != "claude-opus-5-5") > max_spend:
        raise typer.BadParameter("Tinker estimate exceeds --max-spend")
    load_tinker_key()
    for item in [m for m in models.split(",") if m]:
        m, _, renderer_name = item.partition(":")  # model[:renderer] - the renderer picks reasoning on/off
        renderer_name = renderer_name or ZERO_SHOT[m]
        name = f"zeroshot_{m.split('/')[-1]}" + ("" if renderer_name == ZERO_SHOT[m] else f"+{renderer_name}")
        _tinker_judge(m, renderer_name, None, rows, name, max_tokens, typer.echo)
    if opus:
        from eval.anthropic_client import load_api_key

        load_api_key()
        import anthropic

        client = anthropic.Anthropic(max_retries=4)
        outputs, cost = [], 0.0
        for r in rows:
            msgs = r["messages"][:-1]
            with client.messages.stream(model="claude-opus-5-5", max_tokens=2000, system=msgs[0]["content"],
                                        messages=[msgs[1]], output_config={"effort": "medium"}) as stream:
                msg = stream.get_final_message()
            outputs.append("".join(b.text for b in msg.content if b.type == "text"))
            cost += (msg.usage.input_tokens * ANTHROPIC_PRICES["claude-opus-5-5"]["input"] + msg.usage.output_tokens * ANTHROPIC_PRICES["claude-opus-5-5"]["output"]) / 1e6
        path = _write_judgements("zeroshot_claude-opus-5-5", rows, outputs, cost)
        typer.echo(f"opus: {len(rows)} judgements, est ${cost:.3f}, {path.relative_to(ROOT)}")


@app.command("trained")
def trained(run_id: str = typer.Option(...), max_tokens: int = typer.Option(8), yes: bool = typer.Option(False, "--yes")) -> None:
    """Judge the test set with a trained judge checkpoint (run_id in results/train/checkpoints.json)."""
    ck = next(r for r in json.loads(CHECKPOINTS_PATH.read_text()) if r["run_id"] == run_id)
    rows = _test_rows()
    if not yes:
        raise typer.BadParameter(f"{len(rows)} judgements on {ck['model']} (cents); pass --yes")
    load_tinker_key()
    _tinker_judge(ck["model"], ck["renderer"], ck["sampler_path"], rows, f"trained_{ck['model'].split('/')[-1]}_{run_id}", max_tokens, typer.echo)


def kappa(a: list[str], b: list[str]) -> float:
    n = len(a)
    po = sum(x == y for x, y in zip(a, b)) / n
    ca, cb = Counter(a), Counter(b)
    pe = sum(ca[k] * cb[k] for k in set(ca) | set(cb)) / (n * n)
    return (po - pe) / (1 - pe) if pe < 1 else 1.0


def metrics_for(rows: list[dict[str, Any]], metas) -> dict[str, Any]:
    truth = [r["label"] for r in rows]
    pred = [r["predicted"] or "unparsed" for r in rows]
    n = len(rows)
    out: dict[str, Any] = {"n": n, "unparsed": pred.count("unparsed"), "accuracy": wilson(sum(t == p for t, p in zip(truth, pred)), n),
                           "kappa_4class": round(kappa(truth, pred), 3)}
    for lab in LABELS:
        tp = sum(t == lab and p == lab for t, p in zip(truth, pred))
        fp = sum(t != lab and p == lab for t, p in zip(truth, pred))
        fn = sum(t == lab and p != lab for t, p in zip(truth, pred))
        out[f"{lab}_precision"] = wilson(tp, tp + fp) if tp + fp else None
        out[f"{lab}_recall"] = wilson(tp, tp + fn) if tp + fn else None
    out["unsafe_as_pass"] = wilson(sum(t == "leak" and p == "pass" for t, p in zip(truth, pred)), truth.count("leak")) if truth.count("leak") else None
    out["confusion"] = {t: dict(Counter(p for tt, p in zip(truth, pred) if tt == t)) for t in LABELS}
    by_trap: dict[str, list[bool]] = defaultdict(list)
    for r, p in zip(rows, pred):
        if r["label"] == "leak":
            for trap in metas[r["task_id"]].traps:
                by_trap[trap].append(p == "leak")
    out["leak_recall_by_task_trap"] = {k: {"recall": round(sum(v) / len(v), 2), "n": len(v)} for k, v in sorted(by_trap.items())}
    return out


@app.command()
def evaluate() -> None:
    """Metrics for every judgement file under results/judge/ -> results/judge/summary.json."""
    metas = load_task_meta()
    summary = {}
    for path in sorted(JUDGE_DIR.glob("*.jsonl")):
        rows = [json.loads(line) for line in path.read_text().splitlines()]
        cost_path = JUDGE_DIR / f"{path.stem}.cost.json"
        summary[path.stem] = {**metrics_for(rows, metas), "est_spend_usd": json.loads(cost_path.read_text())["est_spend_usd"] if cost_path.exists() else None}
    (JUDGE_DIR / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    for name, m in summary.items():
        lr = m["leak_recall"]["rate"] if m["leak_recall"] else float("nan")
        lp = m["leak_precision"]["rate"] if m["leak_precision"] else float("nan")
        typer.echo(f"{name:45} acc {m['accuracy']['rate']:.0%}  kappa {m['kappa_4class']:.2f}  leak recall {lr:.0%}  leak precision {lp:.0%}  unparsed {m['unparsed']}")


if __name__ == "__main__":
    app()
