from pathlib import Path

import pytest

from harness.models import Task

TASKS_DIR = Path(__file__).resolve().parent.parent / "tasks"


@pytest.fixture(scope="session")
def notes_task() -> Task:
    return Task.load(next(TASKS_DIR.glob("T001-*")))
