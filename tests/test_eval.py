import json

import pytest

from eval import openrouter, run_baselines
from eval.metrics import cohen_kappa, model_metrics, pass_at_k, summarize, wilson
from eval.prompts import build_messages, prompt_hash
from tests.conftest import TASKS_DIR
from harness.models import Task


def test_wilson_and_pass_at_k():
    w = wilson(5, 10)
    assert w["rate"] == 0.5 and 0.2 < w["lo"] < 0.5 < w["hi"] < 0.8
    assert pass_at_k(5, 0, 5) == 0.0
    assert pass_at_k(5, 1, 5) == 1.0
    assert pass_at_k(10, 1, 1) == pytest.approx(0.1)
    assert cohen_kappa([True, False, True, False], [True, False, True, False]) == 1.0


def test_prompt_is_stable_and_hides_rows(notes_task):
    m1, m2 = build_messages(notes_task), build_messages(notes_task)
    assert prompt_hash(m1) == prompt_hash(m2)
    user = m1[1]["content"]
    assert "R1." in user and "public.notes: 4 rows" in user
    assert "ana private" not in user  # seed rows are never shown
    assert notes_task.solution_sql.strip() not in user


def test_run_model_offline(tmp_path, monkeypatch, notes_task):
    """Fake OpenRouter: first sample returns the reference, the rest return no policies."""
    monkeypatch.setattr(run_baselines, "BASELINES_DIR", tmp_path)
    monkeypatch.setattr(openrouter, "model_info", lambda m: {"supported_parameters": ["temperature"]})

    def fake_complete(model, messages, *, prompt_hash, temperature, index, max_tokens, send_temperature, client, reasoning=None):
        sql = notes_task.solution_sql if temperature == 0.0 or index == 0 else "select 1;"
        return openrouter.Completion(f"```sql\n{sql}\n```", {}, 0.01, "fake", "stop", False)

    monkeypatch.setattr(openrouter, "complete", fake_complete)
    out = run_baselines.run_model("fake/model", [notes_task], k=5, max_tokens=100, max_spend=1.0, log=lambda s: None)
    assert out["graded"] == 6 and out["spent_usd"] == pytest.approx(0.06)

    again = run_baselines.run_model("fake/model", [notes_task], k=5, max_tokens=100, max_spend=1.0, log=lambda s: None)
    assert again["graded"] == 0  # nothing re-run

    records = [json.loads(l) for l in (tmp_path / "fake__model.jsonl").read_text().splitlines()]
    from eval.metrics import load_task_meta
    m = model_metrics(records, load_task_meta())
    assert m["pass_at_1"]["rate"] == 1.0
    assert m["pass_at_5"]["rate"] == 1.0
    assert m["format_error_rate"]["rate"] == 0.0

    summary = summarize(tmp_path, tmp_path / "summary.json")
    assert "fake__model" in summary["models"]


def test_spend_cap_stops_submission(tmp_path, monkeypatch, notes_task):
    monkeypatch.setattr(run_baselines, "BASELINES_DIR", tmp_path)
    monkeypatch.setattr(openrouter, "model_info", lambda m: {"supported_parameters": []})
    monkeypatch.setattr(
        openrouter, "complete",
        lambda *a, **kw: openrouter.Completion("no block", {}, 0.5, "fake", "stop", False),
    )
    out = run_baselines.run_model("fake/cap", [notes_task], k=5, max_tokens=100, max_spend=0.9, concurrency=1, log=lambda s: None)
    assert out["stopped_at_cap"] and out["graded"] == 2


def test_reasoning_off_is_sent_recorded_and_kept_separate(tmp_path, monkeypatch, notes_task):
    monkeypatch.setattr(run_baselines, "BASELINES_DIR", tmp_path)
    monkeypatch.setattr(openrouter, "model_info", lambda m: {"supported_parameters": ["temperature", "reasoning"]})
    seen = []

    def fake_complete(model, messages, *, reasoning=None, **kw):
        seen.append(reasoning)
        usage = {"completion_tokens_details": {"reasoning_tokens": 0}}
        return openrouter.Completion(f"```sql\n{notes_task.solution_sql}\n```", usage, 0.001, "fake", "stop", False)

    monkeypatch.setattr(openrouter, "complete", fake_complete)
    out = run_baselines.run_model("fake/model", [notes_task], k=5, max_tokens=4096, max_spend=1.0, reasoning="off", log=lambda s: None)
    assert out["graded"] == 6 and not out["stopped_at_cap"]
    assert seen == [{"enabled": False}] * 6
    path = tmp_path / "fake__model@reasoning-off.jsonl"
    records = [json.loads(l) for l in path.read_text().splitlines()]
    assert {r["reasoning"] for r in records} == {"off"} and {r["reasoning_tokens"] for r in records} == {0}
    assert not (tmp_path / "fake__model.jsonl").exists()


def test_reasoning_off_stops_if_model_still_reasons(tmp_path, monkeypatch, notes_task):
    monkeypatch.setattr(run_baselines, "BASELINES_DIR", tmp_path)
    monkeypatch.setattr(openrouter, "model_info", lambda m: {"supported_parameters": ["temperature", "reasoning"]})
    usage = {"completion_tokens_details": {"reasoning_tokens": 812}}
    monkeypatch.setattr(
        openrouter, "complete",
        lambda *a, **kw: openrouter.Completion("```sql\nselect 1;\n```", usage, 0.001, "fake", "stop", False),
    )
    out = run_baselines.run_model("fake/r", [notes_task], k=5, max_tokens=4096, max_spend=1.0, concurrency=1, reasoning="off", log=lambda s: None)
    assert out["stop_reason"] == "reasoning-not-disabled" and out["graded"] == 1  # nothing sent after the first
