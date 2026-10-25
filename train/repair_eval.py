"""Multi-turn (repair) evaluation: pass rate after 1, 2 and 3 tries with harness feedback between tries.

Protocol per task: 1 greedy sample + k at temperature 0.7 for the first try (as in the baseline protocol);
each sample then gets up to `max_turns - 1` more tries, each prompted with the feedback from
train/rl_env.feedback (failing tests, rules, SQL error; never expected rows or test queries). A sample
that passes stops. Records go to results/repair_eval/<label>.jsonl; the summary has pass-by-try.
"""

from __future__ import annotations

import asyncio
import datetime as dt
import json
from pathlib import Path
from typing import Any, Callable

from eval.metrics import wilson
from eval.prompts import build_messages, prompt_hash
from eval.run_baselines import GREEDY_TEMPERATURE, SAMPLE_TEMPERATURE, tests_hash
from harness.db import ROOT
from harness.models import Task
from harness.runner import run_completion
from train import rl_env
from train.prices import price

REPAIR_DIR = ROOT / "results" / "repair_eval"


def results_path(label: str, out_dir: Path = REPAIR_DIR) -> Path:
    return out_dir / f"{label}.jsonl"


def repair_sample_and_grade(client, renderer, tasks: list[Task], *, label: str, model: str, model_path: str | None,
                            renderer_name: str, k: int = 5, max_turns: int = 3, max_tokens: int = 4096,
                            max_spend: float = 2.0, out_dir: Path = REPAIR_DIR, log: Callable[[str], None] = print) -> dict[str, Any]:
    import tinker
    from tinker_cookbook.renderers import get_text_content

    out_path = results_path(label, out_dir)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    done = set()
    if out_path.exists():
        done = {(r["task_id"], r["temperature"], r["index"]) for r in map(json.loads, out_path.read_text().splitlines())}
    p = price(model)
    stop = renderer.get_stop_sequences()
    run_date = dt.datetime.now(dt.timezone.utc).date().isoformat()
    # Live conversations: one per (task, temperature, index); each round samples one turn for every live one.
    live: list[dict[str, Any]] = []
    for t in tasks:
        base = build_messages(t)
        for temperature, indices in ((GREEDY_TEMPERATURE, [0]), (SAMPLE_TEMPERATURE, list(range(k)))):
            for i in indices:
                if (t.id, temperature, i) in done:
                    continue
                live.append({"task": t, "temperature": temperature, "index": i, "convo": list(base), "turns": [], "passed": False})
    log(f"{label}: {len(live)} conversations, up to {max_turns} tries each ({len(done)} already recorded)")
    spent, graded, stopped = 0.0, 0, False
    for turn in range(max_turns):
        active = [c for c in live if not c["passed"] and len(c["turns"]) == turn]
        if not active:
            break
        futures = []
        for c in active:
            prompt = renderer.build_generation_prompt(c["convo"])
            worst = (prompt.length * p["prefill"] + max_tokens * p["sample"]) / 1e6
            if spent + sum(w for _, _, w in futures) + worst > max_spend:
                stopped = True
                break
            params = tinker.SamplingParams(max_tokens=max_tokens, temperature=c["temperature"], stop=stop, seed=c["index"] + 7 * turn)
            futures.append((c, client.sample(prompt, num_samples=1, sampling_params=params), worst))
        if stopped:
            log(f"spend cap ${max_spend:.2f} would be passed at try {turn + 1}; stopping")
        for c, fut, _ in futures:
            seq = fut.result().sequences[0]
            message, termination = renderer.parse_response(seq.tokens)
            text = get_text_content(message)
            prompt_len = renderer.build_generation_prompt(c["convo"]).length
            spent += (prompt_len * p["prefill"] + len(seq.tokens) * p["sample"]) / 1e6
            result = run_completion(c["task"], text)
            c["turns"].append({"try": turn + 1, "completion": text, "completion_tokens": len(seq.tokens),
                               "termination": str(termination), "result": result.model_dump()})
            c["passed"] = result.passed
            c["convo"] = c["convo"] + [message]
            if not result.passed and turn + 1 < max_turns:
                c["convo"] = c["convo"] + [{"role": "user", "content": rl_env.feedback(c["task"], result)}]
        if stopped:
            break
    for c in live:
        if not c["turns"]:
            continue
        tries = c["turns"]
        record = {
            "model": label, "task_id": c["task"].id, "temperature": c["temperature"], "temperature_sent": True,
            "index": c["index"], "max_tokens": max_tokens, "max_turns": max_turns, "prompt_hash": prompt_hash(build_messages(c["task"])),
            "tests_hash": tests_hash(c["task"]), "run_date": run_date, "provider": "tinker", "model_path": model_path,
            "renderer": renderer_name, "tries": len(tries), "passed": c["passed"],
            "pass_by_try": [any(t["result"]["passed"] for t in tries[:n + 1]) for n in range(max_turns)],
            "leak_any_try": any(bool(t["result"]["leak"]) for t in tries), "final_result": tries[-1]["result"], "turns": tries,
        }
        with out_path.open("a") as f:
            f.write(json.dumps(record) + "\n")
        graded += 1
    return {"graded": graded, "spent_usd": spent, "stopped_at_cap": stopped}


def summarize(label: str, tasks: list[Task], out_dir: Path = REPAIR_DIR) -> dict[str, Any]:
    ids = {t.id for t in tasks}
    rows = [r for r in map(json.loads, results_path(label, out_dir).read_text().splitlines()) if r["task_id"] in ids]
    n = len(rows)
    max_turns = rows[0]["max_turns"] if rows else 0
    by_try = [wilson(sum(r["pass_by_try"][i] for r in rows), n) for i in range(max_turns)]
    greedy = [r for r in rows if r["temperature"] == 0.0]
    return {"label": label, "samples": n, "pass_by_try": by_try,
            "greedy_pass_by_try": [wilson(sum(r["pass_by_try"][i] for r in greedy), len(greedy)) for i in range(max_turns)] if greedy else None,
            "leak_any_try": wilson(sum(r["leak_any_try"] for r in rows), n), "mean_tries": sum(r["tries"] for r in rows) / n if n else None,
            "final_leak": wilson(sum(bool(r["final_result"]["leak"]) for r in rows), n)}


class RepairDevEvaluator:
    """Dev evaluator for repair training: pass after `max_turns` tries over all dev samples."""

    def __init__(self, prefix: str, model_name: str, renderer_name: str, log_path: Path, *, k: int = 5, max_turns: int = 3,
                 max_tokens: int = 4096, max_spend: float = 2.0):
        self.prefix, self.model_name, self.renderer_name, self.log_path = prefix, model_name, renderer_name, log_path
        self.k, self.max_turns, self.max_tokens, self.max_spend = k, max_turns, max_tokens, max_spend
        self.n = 0

    async def __call__(self, sampling_client) -> dict[str, float]:
        from train import eval_tinker

        self.n += 1
        label = f"{self.prefix}-eval{self.n:03d}"
        tasks = eval_tinker.split_tasks("dev")
        renderer = rl_env.make_renderer(self.model_name, self.renderer_name)
        out = await asyncio.to_thread(repair_sample_and_grade, sampling_client, renderer, tasks, label=label, model=self.model_name,
                                      model_path=None, renderer_name=self.renderer_name, k=self.k, max_turns=self.max_turns,
                                      max_tokens=self.max_tokens, max_spend=self.max_spend, log=lambda _: None)
        s = summarize(label, tasks)
        metrics = {f"dev/pass_try{i + 1}": w["rate"] for i, w in enumerate(s["pass_by_try"])}
        metrics.update({"dev/pass_all": s["pass_by_try"][0]["rate"], "dev/pass_final": s["pass_by_try"][-1]["rate"],
                        "dev/leak_any_try": s["leak_any_try"]["rate"], "dev/leak_all": s["final_leak"]["rate"],
                        "dev/mean_tries": s["mean_tries"], "dev/spend_usd": out["spent_usd"]})
        with (self.log_path / "dev_evals.jsonl").open("a") as f:
            f.write(json.dumps({"eval": self.n, "label": label, **metrics}) + "\n")
        return metrics
