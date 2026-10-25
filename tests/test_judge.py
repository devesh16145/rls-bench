import pytest

from train import judge


def test_label_of_orders_pass_leak_error_block():
    assert judge.label_of({"passed": True}) == "pass"
    assert judge.label_of({"passed": False, "leak": True, "apply_error": "x"}) == "leak"
    assert judge.label_of({"passed": False, "leak": False, "apply_error": "syntax"}) == "error"
    assert judge.label_of({"passed": False, "leak": False, "format_error": "no block"}) == "error"
    assert judge.label_of({"passed": False, "leak": False, "block": True}) == "block"
    assert judge.label_of({"passed": False, "leak": False}) == "block"


def test_parse_label_takes_last_known_word():
    assert judge.parse_label("Leak.") == "leak"
    assert judge.parse_label("The candidate would PASS all rules") == "pass"
    assert judge.parse_label("Not a leak. Final answer: block") == "block"
    assert judge.parse_label("unsure") is None


def test_kappa_perfect_and_chance():
    assert judge.kappa(["pass", "leak", "block"], ["pass", "leak", "block"]) == pytest.approx(1.0)
    assert judge.kappa(["pass", "leak", "pass", "leak"], ["pass", "pass", "leak", "leak"]) == pytest.approx(0.0)


def test_balance_caps_each_label_and_is_deterministic():
    rows = [{"label": lab, "i": i} for lab in judge.LABELS for i in range(10)] + [{"label": "pass", "i": 99}]
    kept = judge.balance(rows, per_label=3, seed=1)
    assert len(kept) == 12 and all(sum(r["label"] == lab for r in kept) == 3 for lab in judge.LABELS)
    assert kept == judge.balance(rows, per_label=3, seed=1)


def test_judge_data_respects_split(tmp_path):
    import json

    from harness import split as splitmod

    split = splitmod.load()
    for name in ("train", "dev", "test"):
        rows = [json.loads(line) for line in (judge.DATA_DIR / f"judge_{name}.jsonl").read_text().splitlines()]
        assert rows and {r["task_id"] for r in rows} <= set(split[name])
        assert all(r["messages"][-1]["content"] in judge.LABELS for r in rows)
