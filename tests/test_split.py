import pytest

from harness import split as splitmod
from harness.models import Task
from tests.conftest import TASKS_DIR


def test_make_split_is_deterministic_and_stratified():
    tasks = [Task.load(p) for p in sorted(TASKS_DIR.glob("T*"))]
    a, b = splitmod.make_split(tasks), splitmod.make_split(tasks)
    assert {k: a[k] for k in ("train", "dev", "test")} == {k: b[k] for k in ("train", "dev", "test")}
    for tier, counts in a["per_tier"].items():
        assert counts["test"] >= 1 and counts["dev"] >= 1


@pytest.mark.skipif(not splitmod.SPLIT_PATH.exists(), reason="split not frozen yet")
def test_frozen_split_is_disjoint_and_complete():
    s = splitmod.load()
    train, dev, test = set(s["train"]), set(s["dev"]), set(s["test"])
    assert not (train & dev) and not (train & test) and not (dev & test)
    on_disk = {Task.load(p).id for p in TASKS_DIR.glob("T*") if (p / "task.yaml").exists()}
    assert train | dev | test <= on_disk
    assert s["counts"] == {"train": len(train), "dev": len(dev), "test": len(test)}


def test_freeze_refuses_to_overwrite(tmp_path, monkeypatch):
    target = tmp_path / "split.json"
    target.write_text("{}")
    monkeypatch.setattr(splitmod, "SPLIT_PATH", target)
    with pytest.raises(FileExistsError):
        splitmod.freeze([])


def test_extend_train_refuses_unverified_and_keeps_dev_test(tmp_path, monkeypatch):
    import json
    from pathlib import Path

    import pytest

    from harness import split as splitmod
    from harness.models import Task

    src = splitmod.load()
    trimmed = {**src, "train": [t for t in src["train"] if t != "T104"]}
    path = tmp_path / "split.json"
    path.write_text(json.dumps(trimmed))
    monkeypatch.setattr(splitmod, "SPLIT_PATH", path)
    task = Task.load(next((Path(__file__).resolve().parent.parent / "tasks").glob("T104-*")))
    task.meta.verified = False
    with pytest.raises(ValueError):
        splitmod.extend_train([task])
    task.meta.verified = True
    out = splitmod.extend_train([task])
    assert out["dev"] == src["dev"] and out["test"] == src["test"]
    assert "T104" in out["train"] and len(out["train"]) == len(trimmed["train"]) + 1
    assert out["revisions"][-1]["added_to_train"] == ["T104"]
