"""Freeze the train/dev/test split once (spec §8.1). Stratified by tier, fixed seed."""

from __future__ import annotations

import datetime as dt
import json
import random
from collections import defaultdict
from pathlib import Path

from harness.models import Task

SPLIT_PATH = Path(__file__).resolve().parent.parent / "tasks" / "split.json"
SEED = 20261025
FRACTIONS = {"test": 0.2, "dev": 0.1}  # the rest is train


def make_split(tasks: list[Task], seed: int = SEED) -> dict:
    by_tier: dict[int, list[str]] = defaultdict(list)
    for t in tasks:
        by_tier[t.meta.tier].append(t.id)
    rng = random.Random(seed)
    split: dict[str, list[str]] = {"train": [], "dev": [], "test": []}
    per_tier = {}
    for tier in sorted(by_tier):
        ids = sorted(by_tier[tier])
        rng.shuffle(ids)
        n_test = round(len(ids) * FRACTIONS["test"])
        n_dev = round(len(ids) * FRACTIONS["dev"])
        split["test"] += ids[:n_test]
        split["dev"] += ids[n_test:n_test + n_dev]
        split["train"] += ids[n_test + n_dev:]
        per_tier[str(tier)] = {"train": len(ids) - n_test - n_dev, "dev": n_dev, "test": n_test}
    return {
        "frozen_on": dt.date.today().isoformat(),
        "seed": seed,
        "method": "stratified by tier; per tier: test = round(20%), dev = round(10%), rest train; ids sorted then shuffled with random.Random(seed)",
        "counts": {k: len(v) for k, v in split.items()},
        "per_tier": per_tier,
        **{k: sorted(v) for k, v in split.items()},
    }


def freeze(tasks: list[Task]) -> dict:
    if SPLIT_PATH.exists():
        raise FileExistsError(f"{SPLIT_PATH} already exists; the split is frozen and must never be edited")
    unverified = [t.id for t in tasks if not t.meta.verified]
    if unverified:
        raise ValueError(f"refusing to freeze with unverified tasks: {', '.join(unverified)}")
    split = make_split(tasks)
    SPLIT_PATH.write_text(json.dumps(split, indent=2) + "\n")
    return split


def load() -> dict:
    return json.loads(SPLIT_PATH.read_text())
