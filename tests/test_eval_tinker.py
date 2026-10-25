import pytest
import typer

from harness import split as splitmod
from train import eval_tinker


def test_split_tasks_rejects_tasks_outside_the_split():
    train_task = splitmod.load()["train"][0]
    with pytest.raises(typer.BadParameter):
        eval_tinker.split_tasks("dev", [train_task])


def test_split_tasks_returns_dev_tasks_in_order():
    assert [t.id for t in eval_tinker.split_tasks("dev")] == sorted(splitmod.load()["dev"])


def test_estimate_counts_greedy_plus_k_samples():
    est = eval_tinker.estimate({"T1": 1000, "T2": 2000}, eval_tinker.DEFAULT_MODEL, k=5, max_tokens=4096)
    assert est["samples"] == 12
    assert est["prefill_tokens"] == 18_000
    assert est["worst_usd"] == pytest.approx((18_000 * 0.184 + 12 * 4096 * 0.495) / 1e6)


def test_unknown_checkpoint_is_refused():
    with pytest.raises(typer.BadParameter):
        eval_tinker.checkpoint("no-such-run")


def test_test_split_is_refused():
    with pytest.raises(typer.BadParameter):
        eval_tinker.main(run_id="x", base=False, model=eval_tinker.DEFAULT_MODEL, split_name="test", task=None,
                         k=5, max_tokens=4096, max_spend=1.0, estimate_only=True, yes=False)
