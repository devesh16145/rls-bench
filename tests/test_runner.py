from harness.mutations import validate_task
from harness.runner import run_candidate, run_completion

from tests.conftest import TASKS_DIR
from harness.models import Task


def test_reference_passes_and_is_deterministic(notes_task):
    a = run_candidate(notes_task, notes_task.solution_sql)
    b = run_candidate(notes_task, notes_task.solution_sql)
    assert a.passed
    assert [t.model_dump() for t in a.tests] == [t.model_dump() for t in b.tests]


def test_no_policies_leaks(notes_task):
    result = run_candidate(notes_task, "")
    assert not result.passed and result.leak


def test_format_error_is_not_applied(notes_task):
    result = run_candidate(notes_task, "delete from notes;")
    assert result.format_error and not result.tests


def test_apply_error_is_reported(notes_task):
    result = run_candidate(notes_task, "create policy p on missing_table for select using (true);")
    assert result.apply_error and result.apply_error.startswith("42P01")


def test_completion_without_block_is_format_error(notes_task):
    assert run_completion(notes_task, "alter table notes enable row level security;").format_error


def test_every_task_validates():
    for path in sorted(TASKS_DIR.glob("T*")):
        checks, _ = validate_task(Task.load(path))
        failed = [f"{c.name}: {c.detail}" for c in checks if not c.ok]
        assert not failed, f"{path.name}: {failed}"


def test_results_do_not_depend_on_test_order():
    task = Task.load(next(TASKS_DIR.glob("T011-*")))
    forward = run_candidate(task, task.solution_sql)
    reversed_task = task.model_copy(update={"tests": list(reversed(task.tests))})
    backward = run_candidate(reversed_task, task.solution_sql)
    by_name = {t.name: t.observed for t in backward.tests}
    assert forward.passed and backward.passed
    assert all(by_name[t.name] == t.observed for t in forward.tests)
