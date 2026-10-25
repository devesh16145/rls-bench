import json

import pytest
import typer

from train import test_eval


def _content(k=5):
    models = test_eval.models_to_test(test_eval.DEFAULT_SFT_RUN, test_eval.DEFAULT_RL_RUN, None)
    return test_eval.lock_content(models, ["T001", "T002"], k, 4096)


def test_models_default_to_best_dev_rl_step():
    models = test_eval.models_to_test(test_eval.DEFAULT_SFT_RUN, test_eval.DEFAULT_RL_RUN, None)
    assert [m["name"] for m in models] == ["base", "sft", "sft+rl"]
    assert models[0]["model_path"] is None
    assert models[2]["label"].endswith("-step0015") and models[2]["model_path"].endswith("step_0015")


def test_unsaved_rl_step_is_refused():
    with pytest.raises(typer.BadParameter):
        test_eval.models_to_test(test_eval.DEFAULT_SFT_RUN, test_eval.DEFAULT_RL_RUN, 7)


def test_no_lock_means_first_run(tmp_path):
    assert test_eval.check_lock(tmp_path / "LOCK.json", _content()) is False


def test_identical_lock_allows_resume(tmp_path):
    lock = tmp_path / "LOCK.json"
    lock.write_text(json.dumps({**_content(), "created": "x", "git_commit": "abc"}))
    assert test_eval.check_lock(lock, _content()) is True


def test_different_setup_is_refused_once_locked(tmp_path, monkeypatch):
    monkeypatch.setattr(test_eval, "ROOT", tmp_path)
    lock = tmp_path / "LOCK.json"
    lock.write_text(json.dumps({**_content(), "created": "x", "git_commit": "abc"}))
    with pytest.raises(typer.BadParameter):
        test_eval.check_lock(lock, _content(k=3))
