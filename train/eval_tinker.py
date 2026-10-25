"""Evaluate a Tinker model (a trained checkpoint or the base model) on held-out tasks.

Same protocol as the OpenRouter baselines (spec §7): the fixed prompt, one greedy sample and k samples
at temperature 0.7 per task, every sample graded by the harness. Records use the baseline format, so
`eval.metrics.model_metrics` scores them unchanged. Raw lines go to results/tinker_eval/<label>.jsonl.

`--estimate` renders every prompt locally and prints exact prompt tokens and a cost range; it makes no
Tinker call. Only dev tasks are allowed by default; the test split stays untouched until the final eval.
"""

from __future__ import annotations

import datetime as dt
import json
import warnings
from pathlib import Path
from typing import Any, Callable

import typer

warnings.filterwarnings("ignore", message=r'Field "model_')  # noisy pydantic warnings from tinker

from eval.metrics import load_task_meta, model_metrics  # noqa: E402
from eval.prompts import build_messages, prompt_hash  # noqa: E402
from eval.run_baselines import GREEDY_TEMPERATURE, SAMPLE_TEMPERATURE, tests_hash  # noqa: E402
from harness import split as splitmod  # noqa: E402
from harness.db import ROOT  # noqa: E402
from harness.models import Task  # noqa: E402
from harness.runner import run_completion  # noqa: E402
from train.sft_tinker import CHECKPOINTS_PATH, DEFAULT_MODEL, DEFAULT_RENDERER, load_tinker_key, make_renderer  # noqa: E402

TASKS_DIR = ROOT / "tasks"
EVAL_DIR = ROOT / "results" / "tinker_eval"
# Tinker list prices, USD per 1M tokens, from thinkingmachines.ai/tinker/pricing as of 2026-10-19
# (Nemotron-3.5-Lightning shown at 50% off). Recheck before large runs.
SAMPLE_PRICES = {"nvidia/NVIDIA-Nemotron-3.5-Lightning-30B-A3B-BF16": {"prefill": 0.184, "sample": 0.495}}
TYPICAL_OUTPUT_TOKENS = 1500

app = typer.Typer(add_completion=False)


def split_tasks(split_name: str, task_ids: list[str] | None = None) -> list[Task]:
    split = splitmod.load()
    ids = sorted(split[split_name])
    if task_ids:
        unknown = sorted(set(task_ids) - set(ids))
        if unknown:
            raise typer.BadParameter(f"not in the {split_name} split: {unknown}")
        ids = [i for i in ids if i in task_ids]
    return [Task.load(next(TASKS_DIR.glob(f"{tid}-*"))) for tid in ids]


def checkpoint(run_id: str) -> dict[str, Any]:
    records = json.loads(CHECKPOINTS_PATH.read_text())
    matches = [r for r in records if r["run_id"] == run_id]
    if not matches:
        raise typer.BadParameter(f"no checkpoint with run_id {run_id} in {CHECKPOINTS_PATH.relative_to(ROOT)}")
    return matches[-1]


def results_path(label: str) -> Path:
    return EVAL_DIR / f"{label}.jsonl"


def estimate(prompt_tokens: dict[str, int], model: str, k: int, max_tokens: int) -> dict[str, Any]:
    price = SAMPLE_PRICES[model]
    samples = len(prompt_tokens) * (1 + k)
    # one request per (task, temperature); the k samples share a prompt but are billed as k prefills here
    prefill = sum(prompt_tokens.values()) * (1 + k)
    typical_out = samples * min(TYPICAL_OUTPUT_TOKENS, max_tokens)
    worst_out = samples * max_tokens
    return {
        "samples": samples,
        "prefill_tokens": prefill,
        "typical_usd": (prefill * price["prefill"] + typical_out * price["sample"]) / 1e6,
        "worst_usd": (prefill * price["prefill"] + worst_out * price["sample"]) / 1e6,
    }


def _done_keys(path: Path) -> set[tuple[str, float, int, str, int]]:
    if not path.exists():
        return set()
    return {(r["task_id"], r["temperature"], r["index"], r["prompt_hash"], r["max_tokens"])
            for r in map(json.loads, path.read_text().splitlines())}


def summarize(label: str, tasks: list[Task]) -> dict[str, Any]:
    records = [json.loads(line) for line in results_path(label).read_text().splitlines()]
    metas = {tid: m for tid, m in load_task_meta().items() if tid in {t.id for t in tasks}}
    return model_metrics(records, metas)


def sample_and_grade(client, renderer, tasks: list[Task], *, label: str, model: str, model_path: str | None,
                     renderer_name: str, k: int, max_tokens: int, max_spend: float,
                     log: Callable[[str], None] = print) -> dict[str, Any]:
    """Sample 1 greedy + k at temperature 0.7 per task from a Tinker SamplingClient, grade, append records.

    Skips samples already recorded under the label; stops before a request whose worst case would pass max_spend.
    """
    import tinker
    from tinker_cookbook.renderers import ParseTermination, get_text_content

    out_path = results_path(label)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    done = _done_keys(out_path)
    price = SAMPLE_PRICES[model]
    messages = {t.id: build_messages(t) for t in tasks}
    prompts = {tid: renderer.build_generation_prompt(m) for tid, m in messages.items()}
    stop = renderer.get_stop_sequences()
    run_date = dt.datetime.now(dt.timezone.utc).date().isoformat()

    # One request per (task, temperature): greedy is index 0; sampled indices are 0..k-1 as in the baselines.
    jobs = []
    for t in tasks:
        ph = prompt_hash(messages[t.id])
        for temperature, indices in ((GREEDY_TEMPERATURE, [0]), (SAMPLE_TEMPERATURE, list(range(k)))):
            todo = [i for i in indices if (t.id, temperature, i, ph, max_tokens) not in done]
            if todo:
                jobs.append((t, ph, temperature, todo))
    log(f"{label}: {sum(len(j[3]) for j in jobs)} samples to run ({len(done)} already recorded)")

    spent, graded, stopped = 0.0, 0, False
    futures = []
    for t, ph, temperature, todo in jobs:
        prompt = prompts[t.id]
        worst = (prompt.length * len(todo) * price["prefill"] + len(todo) * max_tokens * price["sample"]) / 1e6
        if sum(w for *_, w in futures) + worst > max_spend:
            stopped = True
            log(f"spend cap ${max_spend:.2f} would be passed; not submitting the remaining requests")
            break
        params = tinker.SamplingParams(max_tokens=max_tokens, temperature=temperature, stop=stop, seed=todo[0])
        futures.append((t, ph, temperature, todo, client.sample(prompt, num_samples=len(todo), sampling_params=params), worst))

    for t, ph, temperature, todo, fut, _ in futures:
        response = fut.result()
        prompt_len = prompts[t.id].length
        for index, seq in zip(todo, response.sequences):
            message, termination = renderer.parse_response(seq.tokens)
            text = get_text_content(message)
            out_tokens = len(seq.tokens)
            cost = (prompt_len * price["prefill"] + out_tokens * price["sample"]) / 1e6
            spent += cost
            finish = "length" if termination == ParseTermination.MALFORMED and out_tokens >= max_tokens else str(termination)
            result = run_completion(t, text)
            record = {
                "model": label, "task_id": t.id, "temperature": temperature, "temperature_sent": True,
                "reasoning": "off", "reasoning_tokens": 0, "index": index, "max_tokens": max_tokens,
                "prompt_hash": ph, "tests_hash": tests_hash(t), "run_date": run_date, "provider": "tinker",
                "model_path": model_path, "renderer": renderer_name, "finish_reason": finish,
                "usage": {"prompt_tokens": prompt_len, "completion_tokens": out_tokens},
                "cost_usd": round(cost, 6), "completion": text, "result": result.model_dump(),
            }
            with out_path.open("a") as f:
                f.write(json.dumps(record) + "\n")
            graded += 1
            status = "PASS" if result.passed else ("LEAK" if result.leak else "FAIL")
            log(f"  [{graded}] {t.id} t={temperature} #{index} {status}  est spend ${spent:.3f}")
    return {"graded": graded, "spent_usd": spent, "stopped_at_cap": stopped}


@app.command()
def main(
    run_id: str = typer.Option(None, help="Checkpoint run_id from results/train/checkpoints.json; omit with --base."),
    base: bool = typer.Option(False, "--base", help="Sample the untrained base model instead of a checkpoint."),
    model: str = typer.Option(DEFAULT_MODEL, help="Base model (only used with --base)."),
    split_name: str = typer.Option("dev", "--split"),
    task: list[str] = typer.Option(None, "--task", help="Limit to these task ids; repeatable."),
    k: int = typer.Option(5, help="Samples at temperature 0.7 per task (plus one greedy)."),
    max_tokens: int = typer.Option(4096),
    max_spend: float = typer.Option(2.0, help="Stop before a request whose worst case would pass this (USD)."),
    estimate_only: bool = typer.Option(False, "--estimate", help="Print the cost estimate; no Tinker calls."),
    yes: bool = typer.Option(False, "--yes", help="Confirm the spend."),
) -> None:
    if split_name == "test":
        raise typer.BadParameter("the test split is reserved for the final eval (spec §8.1)")
    if base == bool(run_id):
        raise typer.BadParameter("pass exactly one of --run-id or --base")
    if base:
        renderer_name, model_path, label = DEFAULT_RENDERER, None, f"{model.split('/')[-1]}@base"
    else:
        ck = checkpoint(run_id)
        model, renderer_name, model_path = ck["model"], ck["renderer"], ck["sampler_path"]
        label = f"{model.split('/')[-1]}@{ck['kind']}-{run_id}"
    tasks = split_tasks(split_name, task)
    renderer, _ = make_renderer(model, renderer_name)
    messages = {t.id: build_messages(t) for t in tasks}
    prompts = {tid: renderer.build_generation_prompt(m) for tid, m in messages.items()}
    est = estimate({tid: p.length for tid, p in prompts.items()}, model, k, max_tokens)
    typer.echo(json.dumps({"label": label, "model": model, "model_path": model_path, "renderer": renderer_name,
                           "split": split_name, "tasks": len(tasks), "k": k, "max_tokens": max_tokens, **est}, indent=2))
    if estimate_only:
        return
    if not yes:
        raise typer.BadParameter("this spends money: run with --estimate first, then pass --yes")

    load_tinker_key()
    import tinker

    service = tinker.ServiceClient()
    client = (service.create_sampling_client(model_path=model_path) if model_path
              else service.create_sampling_client(base_model=model))
    out = sample_and_grade(client, renderer, tasks, label=label, model=model, model_path=model_path,
                           renderer_name=renderer_name, k=k, max_tokens=max_tokens, max_spend=max_spend, log=typer.echo)
    spent, graded, stopped, out_path = out["spent_usd"], out["graded"], out["stopped_at_cap"], results_path(label)

    m = summarize(label, tasks)
    summary = {"label": label, "graded": graded, "est_spend_usd": round(spent, 4), "stopped_at_cap": stopped,
               "path": str(out_path.relative_to(ROOT)), "metrics": m}
    (EVAL_DIR / f"{label}.summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    typer.echo(json.dumps({k_: summary[k_] for k_ in ("label", "graded", "est_spend_usd", "stopped_at_cap")}
                          | {"pass_at_1": m["pass_at_1"], "pass_at_5": m["pass_at_5"], "leak_rate": m["leak_rate"],
                             "apply_error_rate": m["apply_error_rate"], "format_error_rate": m["format_error_rate"]}, indent=2))


if __name__ == "__main__":
    app()
