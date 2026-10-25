import json

from harness.models import Task
from train import repair_eval


def _row(task_id, temperature, index, passes, leaks):
    tries = [{"try": i + 1, "completion": "", "completion_tokens": 10, "termination": "stop_sequence",
              "result": {"task_id": task_id, "passed": p, "leak": l, "apply_error": None, "format_error": None, "block": False}}
             for i, (p, l) in enumerate(zip(passes, leaks))]
    return {"model": "x", "task_id": task_id, "temperature": temperature, "index": index, "max_turns": 3, "tries": len(tries),
            "passed": passes[-1], "pass_by_try": [any(passes[:n + 1]) for n in range(3)],
            "leak_any_try": any(leaks), "final_result": tries[-1]["result"], "turns": tries}


def test_summarize_pass_by_try(tmp_path):
    rows = [
        _row("T001", 0.0, 0, [True], [False]),                        # passes first try
        _row("T001", 0.7, 0, [False, True], [True, False]),           # leaks, then fixed on try 2
        _row("T001", 0.7, 1, [False, False, False], [False] * 3),     # never passes
        _row("T002", 0.0, 0, [False, False, True], [False] * 3),      # passes on try 3
    ]
    path = tmp_path / "lab.jsonl"
    path.write_text("".join(json.dumps(r) + "\n" for r in rows))
    tasks = [Task.load(next(repair_eval.ROOT.glob("tasks/T001-*"))), Task.load(next(repair_eval.ROOT.glob("tasks/T002-*")))]
    s = repair_eval.summarize("lab", tasks, out_dir=tmp_path)
    assert s["samples"] == 4
    assert [round(w["rate"], 2) for w in s["pass_by_try"]] == [0.25, 0.5, 0.75]
    assert [round(w["rate"], 2) for w in s["greedy_pass_by_try"]] == [0.5, 0.5, 1.0]
    assert s["leak_any_try"]["rate"] == 0.25 and s["final_leak"]["rate"] == 0.0
    assert s["mean_tries"] == 2.25
