from collections import Counter

from harness import split as split_mod
from train import hf_upload


def test_task_rows_cover_every_task_once_with_its_split():
    rows = hf_upload.task_rows()
    split = split_mod.load()
    assert len(rows) == sum(split["counts"].values())
    assert len({r["id"] for r in rows}) == len(rows)
    assert Counter(r["split"] for r in rows) == split["counts"]
    notes = next(r for r in rows if r["id"] == "T001")
    assert notes["n_tests"] > 0 and "R1." in notes["requirement"] and notes["canary"] in notes["requirement"]
    assert notes["trap_files"] and all(set(t) == {"name", "sql"} for t in notes["trap_files"])


def test_adapter_rows_join_manifest_run_and_test_row():
    rows = hf_upload.adapter_rows()
    assert [r["folder"] for r in rows] == [a[0] for a in hf_upload.ADAPTERS]
    for r in rows:
        assert r["n"] == 120 and 0 <= r["pass"]["rate"] <= 1 and r["bytes"] > 0
        assert r["kind"] in ("sft", "rl", "distil")


def test_cards_render_without_placeholders():
    dataset_card, adapters_card = hf_upload.render_cards()
    assert dataset_card.startswith("---\n") and adapters_card.startswith("---\n")
    assert "<!--" not in dataset_card and "<!--" not in adapters_card
    assert adapters_card.count("| `") >= len(hf_upload.ADAPTERS) * 2  # one row per adapter in each table
    assert hf_upload.JUDGE_FOLDER in adapters_card
