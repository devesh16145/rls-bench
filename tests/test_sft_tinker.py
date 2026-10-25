import json

import pytest

from harness import split as splitmod
from train import sft_tinker


def test_load_examples_refuses_dev_and_test_tasks(tmp_path):
    test_task = splitmod.load()["test"][0]
    path = tmp_path / "sft.jsonl"
    path.write_text(json.dumps({"task_id": test_task, "messages": []}) + "\n")
    with pytest.raises(ValueError):
        sft_tinker.load_examples(path)


def test_plan_steps_drops_partial_batches():
    assert sft_tinker.plan_steps(427, 16, 3) == 78


def test_estimate_scales_with_epochs_and_price():
    stats = {"examples": 32, "tokens": 32_000}
    est = sft_tinker.estimate(stats, sft_tinker.DEFAULT_MODEL, epochs=2, batch_size=16)
    assert est["train_tokens"] == 64_000
    assert est["train_usd"] == pytest.approx(64_000 / 1e6 * 0.44)


def test_default_renderer_is_recommended_for_model():
    from tinker_cookbook import model_info

    assert sft_tinker.DEFAULT_RENDERER in model_info.get_recommended_renderer_names(sft_tinker.DEFAULT_MODEL)
