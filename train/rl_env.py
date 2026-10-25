"""The harness as a Tinker cookbook RL environment (spec §8.3).

One episode: the model gets the fixed benchmark prompt for a train task and answers with policies; the
harness grades the answer and the grade is the reward. With `max_turns > 1` a failing answer gets
feedback (which tests failed, which rules they cover, the SQL error if any; never the expected rows or
the test queries) and the model may try again.

Rewards per turn (spec §6.4 plus a leak penalty): 1 pass, 0 safe failure, -0.1 format error,
-leak_penalty for a leak; turns after the first also cost `turn_penalty`. Per-turn rewards are summed
by the cookbook, so with one turn this is exactly the single-answer reward.
"""

from __future__ import annotations

import asyncio
import random
from collections.abc import Sequence
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Callable

import chz
from tinker_cookbook import renderers
from tinker_cookbook.eval.evaluators import SamplingClientEvaluator
from tinker_cookbook.rl.message_env import EnvFromMessageEnv, MessageEnv, MessageStepResult
from tinker_cookbook.rl.types import Env, EnvGroupBuilder, RLDataset, RLDatasetBuilder
from tinker_cookbook.tokenizer_utils import get_tokenizer

from eval.prompts import build_messages
from harness.db import ROOT
from harness.models import Task, TaskResult
from harness.runner import run_completion
from train.rl_tinker import FORMAT_PENALTY, LEAK_PENALTY, reward

TASKS_DIR = ROOT / "tasks"
GRADE_CONCURRENCY = 4  # harness clones a database per candidate; keep Postgres load bounded
MAX_FEEDBACK_TESTS = 12
TURN_PENALTY = 0.05
REPAIR_INSTRUCTION = (
    "Reply with a complete, corrected answer: exactly one ```sql block with the full set of statements, "
    "not a diff."
)

_grade_semaphores: dict[int, asyncio.Semaphore] = {}


@lru_cache(maxsize=None)
def load_task(task_id: str) -> Task:
    return Task.load(next(TASKS_DIR.glob(f"{task_id}-*")))


@lru_cache(maxsize=None)
def task_messages(task_id: str) -> tuple[dict[str, str], ...]:
    """The fixed prompt for a task (seeds a scratch database once per task to describe the data)."""
    return tuple(build_messages(load_task(task_id)))


def make_renderer(model_name: str, renderer_name: str) -> renderers.Renderer:
    return renderers.get_renderer(renderer_name, get_tokenizer(model_name))


async def grade(task: Task, completion: str) -> TaskResult:
    """Grade in a worker thread, at most GRADE_CONCURRENCY at a time per event loop."""
    loop_id = id(asyncio.get_running_loop())
    sem = _grade_semaphores.setdefault(loop_id, asyncio.Semaphore(GRADE_CONCURRENCY))
    async with sem:
        return await asyncio.to_thread(run_completion, task, completion)


def _expect_kind(expect: dict[str, Any]) -> str:
    for kind in ("denied", "error", "rows", "count", "affected"):
        if expect.get(kind) is not None:
            return kind
    return "result"


def feedback(task: Task, result: TaskResult) -> str:
    """What the harness tells the model about a failing answer. Never the expected rows or the test SQL."""
    if result.format_error:
        return f"Your answer could not be used: {result.format_error}. {REPAIR_INSTRUCTION}"
    if result.apply_error:
        return f"Your SQL failed to apply:\n{result.apply_error[:600]}\n\n{REPAIR_INSTRUCTION}"
    covers = {t.name: t.covers for t in task.tests}
    failing = [t for t in result.tests if not t.passed]
    lines = []
    for t in failing[:MAX_FEEDBACK_TESTS]:
        expected = _expect_kind(t.expected)
        obs = t.observed
        if obs.errored:
            observed = f"got error {obs.sqlstate}: {(obs.message or '').strip()[:160]}"
        elif obs.rows is not None:
            observed = f"got {len(obs.rows)} row(s)"
        elif obs.rowcount is not None:
            observed = f"{obs.rowcount} row(s) affected"
        else:
            observed = "no result"
        verdict = "LEAK: access was allowed that must be denied" if t.leak else (
            "BLOCKED: access was denied that must be allowed" if t.block else "wrong result")
        lines.append(f"- {t.name} (rules {', '.join(covers.get(t.name, []))}): {verdict}; expected {expected}, {observed}")
    more = f"\n... and {len(failing) - MAX_FEEDBACK_TESTS} more failing tests" if len(failing) > MAX_FEEDBACK_TESTS else ""
    return (f"{len(failing)} of {len(result.tests)} tests failed:\n" + "\n".join(lines) + more
            + f"\n\n{REPAIR_INSTRUCTION}")


class SpendGuard:
    """Rough running cost of a run from the tokens the environment sees; raises past the cap.

    A backstop only: runs are sized under the cap before they start. Prices are USD per 1M tokens.
    """

    def __init__(self, max_spend: float, prefill: float, sample: float, train: float):
        self.max_spend, self.prefill, self.sample, self.train = max_spend, prefill, sample, train
        self.prompt_tokens = self.completion_tokens = 0

    def add(self, prompt_tokens: int, completion_tokens: int) -> None:
        self.prompt_tokens += prompt_tokens
        self.completion_tokens += completion_tokens
        if self.spent() > self.max_spend:
            raise RuntimeError(f"spend cap ${self.max_spend:.2f} passed (estimated ${self.spent():.2f})")

    def spent(self) -> float:
        # Every sampled token is also trained on (prompt + completion), which is the worst case.
        return (self.prompt_tokens * self.prefill + self.completion_tokens * self.sample
                + (self.prompt_tokens + self.completion_tokens) * self.train) / 1e6


_guards: dict[str, SpendGuard] = {}


def spend_guard(name: str, **prices: float) -> SpendGuard | None:
    """Module-level registry so pickled builders can find their run's guard by name."""
    if name not in _guards and prices:
        _guards[name] = SpendGuard(**prices)
    return _guards.get(name)


class RlsMessageEnv(MessageEnv):
    def __init__(self, task: Task, renderer: renderers.Renderer, *, max_turns: int = 1,
                 leak_penalty: float = LEAK_PENALTY, format_penalty: float = FORMAT_PENALTY,
                 turn_penalty: float = TURN_PENALTY, guard: SpendGuard | None = None, reward_scale: float = 1.0):
        self.task, self.renderer = task, renderer
        self.reward_scale = reward_scale  # 0 for pure distillation: metrics are still logged, the reward is not used
        self.max_turns, self.leak_penalty, self.format_penalty, self.turn_penalty = max_turns, leak_penalty, format_penalty, turn_penalty
        self.guard = guard
        self.convo: list[dict[str, Any]] = list(task_messages(task.id))
        self.turn = 0
        self.results: list[TaskResult] = []

    async def initial_observation(self) -> list[dict[str, Any]]:
        return list(self.convo)

    async def step(self, message: dict[str, Any]) -> MessageStepResult:
        text = renderers.get_text_content(message)
        result = await grade(self.task, text)
        self.turn += 1
        self.results.append(result)
        r = reward(result, self.leak_penalty)
        if result.format_error:
            r = -self.format_penalty
        if self.turn > 1:
            r -= self.turn_penalty
        r *= self.reward_scale
        done = result.passed or self.turn >= self.max_turns
        self.convo = self.convo + [message]
        if self.guard is not None:
            prompt_len = self.renderer.build_generation_prompt(self.convo[:-1]).length
            self.guard.add(prompt_len, len(self.renderer.tokenizer.encode(text)))
        metrics = {
            "pass": float(result.passed), "leak": float(bool(result.leak)), "block": float(bool(result.block)),
            "format_error": float(bool(result.format_error)), "apply_error": float(bool(result.apply_error)),
            "grade_ms": float(result.duration_ms),
        }
        if done:
            metrics["turns"] = float(self.turn)
            metrics["pass_final"] = float(result.passed)
            return MessageStepResult(reward=r, episode_done=True, next_messages=self.convo, metrics=metrics)
        self.convo = self.convo + [{"role": "user", "content": feedback(self.task, result)}]
        return MessageStepResult(reward=r, episode_done=False, next_messages=self.convo, metrics=metrics)


@dataclass(frozen=True)
class RlsEnvGroupBuilder(EnvGroupBuilder):
    task_id: str
    tier: int
    group_size: int
    model_name: str
    renderer_name: str
    max_turns: int = 1
    leak_penalty: float = LEAK_PENALTY
    format_penalty: float = FORMAT_PENALTY
    turn_penalty: float = TURN_PENALTY
    max_tokens: int = 2048
    guard_name: str | None = None
    reward_scale: float = 1.0

    async def make_envs(self) -> Sequence[Env]:
        task = load_task(self.task_id)
        renderer = make_renderer(self.model_name, self.renderer_name)
        guard = spend_guard(self.guard_name) if self.guard_name else None
        return [
            EnvFromMessageEnv(
                renderer,
                RlsMessageEnv(task, renderer, max_turns=self.max_turns, leak_penalty=self.leak_penalty,
                              format_penalty=self.format_penalty, turn_penalty=self.turn_penalty, guard=guard,
                              reward_scale=self.reward_scale),
                failed_parse_reward=-self.format_penalty,
                max_generation_tokens=self.max_tokens,
            )
            for _ in range(self.group_size)
        ]

    def logging_tags(self) -> list[str]:
        return [f"tier{self.tier}"]


def plan_batches(task_ids: Sequence[str], tasks_per_step: int, steps: int, seed: int) -> list[list[str]]:
    """Shuffled epochs over the tasks, `tasks_per_step` at a time, for exactly `steps` steps."""
    rng = random.Random(seed)
    batches: list[list[str]] = []
    order: list[str] = []
    while len(batches) < steps:
        if len(order) < tasks_per_step:
            epoch = list(task_ids)
            rng.shuffle(epoch)
            order += epoch
        batches.append(order[:tasks_per_step])
        order = order[tasks_per_step:]
    return batches


class RlsDataset(RLDataset):
    def __init__(self, builders: dict[str, RlsEnvGroupBuilder], batches: list[list[str]]):
        self.builders, self.batches = builders, batches

    def get_batch(self, index: int) -> Sequence[EnvGroupBuilder]:
        return [self.builders[tid] for tid in self.batches[index]]

    def __len__(self) -> int:
        return len(self.batches)


@chz.chz
class RlsDatasetBuilder(RLDatasetBuilder):
    task_ids: list[str]
    steps: int
    tasks_per_step: int
    group_size: int
    model_name: str
    renderer_name: str
    seed: int = 0
    max_turns: int = 1
    leak_penalty: float = LEAK_PENALTY
    format_penalty: float = FORMAT_PENALTY
    turn_penalty: float = TURN_PENALTY
    max_tokens: int = 2048
    guard_name: str | None = None
    reward_scale: float = 1.0

    async def __call__(self) -> tuple[RLDataset, RLDataset | None]:
        builders = {
            tid: RlsEnvGroupBuilder(task_id=tid, tier=load_task(tid).meta.tier, group_size=self.group_size,
                                    model_name=self.model_name, renderer_name=self.renderer_name,
                                    max_turns=self.max_turns, leak_penalty=self.leak_penalty,
                                    format_penalty=self.format_penalty, turn_penalty=self.turn_penalty,
                                    max_tokens=self.max_tokens, guard_name=self.guard_name, reward_scale=self.reward_scale)
            for tid in self.task_ids
        }
        return RlsDataset(builders, plan_batches(self.task_ids, self.tasks_per_step, self.steps, self.seed)), None


class DevEvaluator(SamplingClientEvaluator):
    """Dev eval with the baseline protocol (1 greedy + k at 0.7), run on each checkpoint the loop offers.

    Records go to results/tinker_eval/<prefix>-eval<n>.jsonl via eval_tinker.sample_and_grade; a one-line
    summary of each eval is appended to `log_path`/dev_evals.jsonl so the run record can pick them up.
    """

    def __init__(self, prefix: str, model_name: str, renderer_name: str, log_path: Path, *, k: int = 5,
                 max_tokens: int = 4096, max_spend: float = 1.0):
        self.prefix, self.model_name, self.renderer_name, self.log_path = prefix, model_name, renderer_name, log_path
        self.k, self.max_tokens, self.max_spend = k, max_tokens, max_spend
        self.n = 0

    async def __call__(self, sampling_client) -> dict[str, float]:
        import json

        from train import eval_tinker

        self.n += 1
        label = f"{self.prefix}-eval{self.n:03d}"
        tasks = eval_tinker.split_tasks("dev")
        renderer = make_renderer(self.model_name, self.renderer_name)
        out = await asyncio.to_thread(
            eval_tinker.sample_and_grade, sampling_client, renderer, tasks, label=label, model=self.model_name,
            model_path=None, renderer_name=self.renderer_name, k=self.k, max_tokens=self.max_tokens,
            max_spend=self.max_spend, log=lambda _: None)
        records = [json.loads(line) for line in eval_tinker.results_path(label).read_text().splitlines()]
        n = len(records)
        greedy = [r for r in records if r["temperature"] == 0.0]
        metrics = {
            "dev/pass_all": sum(r["result"]["passed"] for r in records) / n,
            "dev/leak_all": sum(bool(r["result"]["leak"]) for r in records) / n,
            "dev/apply_error_all": sum(bool(r["result"]["apply_error"]) for r in records) / n,
            "dev/pass_at_1": sum(r["result"]["passed"] for r in greedy) / len(greedy),
            "dev/mean_completion_tokens": sum(r["usage"]["completion_tokens"] for r in records) / n,
            "dev/spend_usd": out["spent_usd"],
        }
        with (self.log_path / "dev_evals.jsonl").open("a") as f:
            f.write(json.dumps({"eval": self.n, "label": label, **metrics}) + "\n")
        return metrics


def make_dev_evaluator(**kwargs: Any) -> Callable[[], SamplingClientEvaluator]:
    evaluator = DevEvaluator(**kwargs)
    return lambda: evaluator
