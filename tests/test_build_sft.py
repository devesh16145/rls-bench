import json

from eval import openrouter
from harness import split as splitmod
from train import build_sft


def test_only_train_tasks_are_used():
    tasks = build_sft.train_tasks()
    split = splitmod.load()
    assert {t.id for t in tasks} == set(split["train"])
    assert not {t.id for t in tasks} & (set(split["dev"]) | set(split["test"]))


def test_normalise_sql_ignores_comments_case_and_spacing():
    a = "-- policy\nCREATE POLICY p ON t\n  FOR SELECT USING (true);"
    b = "create policy p on t for select using (true)"
    assert build_sft.normalise_sql(a) == build_sft.normalise_sql(b)


def test_sample_and_rebuild_offline(tmp_path, monkeypatch):
    monkeypatch.setattr(build_sft, "RAW_PATH", tmp_path / "raw.jsonl")
    monkeypatch.setattr(build_sft, "SFT_PATH", tmp_path / "sft.jsonl")
    monkeypatch.setattr(openrouter, "model_info", lambda m: {"pricing": {"prompt": "0", "completion": "0"}})
    tasks = build_sft.train_tasks(limit=2)

    def fake_complete(model, messages, *, index, **kw):
        task = next(t for t in tasks if t.requirement.strip() in messages[1]["content"])
        if index % 3 == 0:
            body = task.solution_sql  # identical to the reference: must be deduped away
        elif index % 3 == 1:
            body = f"-- variant {index}\n" + task.solution_sql.upper().replace("AUTH.UID()", "auth.uid()")
        else:
            body = "select 1;"  # format error: never kept
        return openrouter.Completion(f"```sql\n{body}\n```", {}, 0.0, "fake", "stop", False)

    monkeypatch.setattr(openrouter, "complete", fake_complete)
    out = build_sft.sample(tasks, model="fake/m", samples=6, max_tokens=100, max_spend=1.0, concurrency=1, log=lambda s: None)
    assert out["graded"] == 12
    again = build_sft.sample(tasks, model="fake/m", samples=6, max_tokens=100, max_spend=1.0, concurrency=1, log=lambda s: None)
    assert again["graded"] == 0  # already recorded

    stats = build_sft.rebuild_sft(max_keep=6, log=lambda s: None)
    rows = [json.loads(l) for l in (tmp_path / "sft.jsonl").read_text().splitlines()]
    assert {r["task_id"] for r in rows} == {t.id for t in tasks}
    for t in tasks:
        mine = [r for r in rows if r["task_id"] == t.id]
        assert sum(r["source"] == "reference" for r in mine) == 1
        keys = [build_sft.normalise_sql(build_sft.extract_sql_block(r["messages"][-1]["content"])) for r in mine]
        assert len(keys) == len(set(keys))  # deduped, and the copy of the reference was dropped
        assert all(r["messages"][0]["role"] == "system" and r["messages"][-1]["role"] == "assistant" for r in mine)
    assert all(s["kept"] <= 6 for s in stats["per_task"].values())
