import json

import pytest

from harness.models import TaskResult
from train import rl_tinker


def _result(**kw) -> TaskResult:
    return TaskResult(task_id="T001", passed=kw.pop("passed", False), **kw)


def test_reward_orders_pass_safe_fail_format_error_and_leak():
    assert rl_tinker.reward(_result(passed=True)) == 1.0
    assert rl_tinker.reward(_result(block=True)) == 0.0
    assert rl_tinker.reward(_result(apply_error="syntax error")) == 0.0
    assert rl_tinker.reward(_result(format_error="no sql block")) == -0.1
    assert rl_tinker.reward(_result(leak=True)) == -0.5
    assert rl_tinker.reward(_result(leak=True), leak_penalty=0.0) == 0.0


def test_kept_tasks_drops_groups_with_identical_rewards(tmp_path):
    path = tmp_path / "filter.jsonl"
    rows = [("A", 1.0), ("A", 1.0), ("B", 0.0), ("B", 0.0), ("C", 0.0), ("C", -0.5), ("D", 1.0), ("D", 0.0)]
    path.write_text("".join(json.dumps({"task_id": t, "reward": r}) + "\n" for t, r in rows))
    assert rl_tinker.kept_tasks(path) == ["C", "D"]


def test_plan_batches_covers_every_task_each_epoch():
    ids = [f"T{i:03d}" for i in range(20)]
    batches = rl_tinker.plan_batches(ids, tasks_per_step=8, steps=5, seed=0)
    assert len(batches) == 5 and all(len(b) == 8 for b in batches)
    assert set(sum(batches[:2], [])) < set(ids) and len(set(sum(batches[:2], []))) == 16
    assert batches == rl_tinker.plan_batches(ids, tasks_per_step=8, steps=5, seed=0)


def test_estimate_rollouts_adds_training_cost():
    sample = rl_tinker.estimate_rollouts([500, 500], 8, 1000, rl_tinker.eval_tinker.DEFAULT_MODEL, train=False)
    both = rl_tinker.estimate_rollouts([500, 500], 8, 1000, rl_tinker.eval_tinker.DEFAULT_MODEL, train=True)
    assert sample["rollouts"] == 16
    assert sample["worst_usd"] == pytest.approx((8000 * 0.184 + 16 * 1000 * 0.495) / 1e6)
    assert both["worst_usd"] == pytest.approx(sample["worst_usd"] + (8000 + 16_000) * 0.44 / 1e6)


def test_sft_checkpoint_rejects_unknown_run():
    import typer

    with pytest.raises(typer.BadParameter):
        rl_tinker.sft_checkpoint("no-such-run")


def test_sign_test_matches_exact_binomial():
    from train.report import sign_test

    assert sign_test(6, 1) == pytest.approx(16 / 128)
    assert sign_test(3, 2) == 1.0
    assert sign_test(0, 0) == 1.0
