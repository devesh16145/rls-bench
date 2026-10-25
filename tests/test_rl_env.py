import asyncio

import pytest

from train import rl_env


def _run(coro):
    return asyncio.run(coro)


def _env(task_id: str, **kw) -> rl_env.RlsMessageEnv:
    return rl_env.RlsMessageEnv(rl_env.load_task(task_id), renderer=None, **kw)


def _answer(sql: str) -> dict:
    return {"role": "assistant", "content": f"```sql\n{sql}\n```"}


def test_reference_scores_one_and_ends_episode():
    env = _env("T001")
    obs = _run(env.initial_observation())
    assert [m["role"] for m in obs] == ["system", "user"]
    step = _run(env.step(_answer(env.task.solution_sql)))
    assert step.reward == 1.0 and step.episode_done and step.metrics["pass"] == 1.0


def test_trap_is_penalised_and_feedback_hides_tests():
    env = _env("T001", max_turns=2)
    trap = next((env.task.path / "traps").glob("*.sql")).read_text()
    step = _run(env.step(_answer(trap)))
    assert step.reward < 0 and not step.episode_done
    fb = step.next_messages[-1]["content"]
    assert "tests failed" in fb and "rules R" in fb
    for t in env.task.tests:
        assert (t.sql or "") not in fb or not t.sql  # the test query itself is never shown
    assert "expected" in fb and "row" in fb or "error" in fb


def test_second_turn_pass_costs_the_turn_penalty():
    env = _env("T001", max_turns=2)
    _run(env.step(_answer("select 1")))
    step = _run(env.step(_answer(env.task.solution_sql)))
    assert step.episode_done and step.reward == pytest.approx(1.0 - rl_env.TURN_PENALTY)
    assert step.metrics["turns"] == 2.0


def test_format_error_feedback_and_penalty():
    env = _env("T001", max_turns=2)
    step = _run(env.step({"role": "assistant", "content": "no sql here"}))
    assert step.reward == pytest.approx(-rl_env.FORMAT_PENALTY)
    assert "could not be used" in step.next_messages[-1]["content"]


def test_plan_batches_cycles_shuffled_epochs():
    ids = [f"T{i:03d}" for i in range(10)]
    batches = rl_env.plan_batches(ids, tasks_per_step=4, steps=5, seed=1)
    assert len(batches) == 5 and all(len(b) == 4 for b in batches)
    assert sorted(sum(batches[:2], []) + batches[2][:2]) == sorted(ids)  # first epoch = first 10 draws
    assert batches == rl_env.plan_batches(ids, tasks_per_step=4, steps=5, seed=1)


def test_spend_guard_raises_past_cap():
    g = rl_env.SpendGuard(max_spend=0.001, prefill=1.0, sample=1.0, train=1.0)
    g.add(100, 100)
    with pytest.raises(RuntimeError):
        g.add(1_000_000, 1_000_000)
