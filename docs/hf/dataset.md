---
pretty_name: RLS-Bench
license: cc-by-4.0
language:
- en
task_categories:
- text-generation
tags:
- sql
- postgres
- supabase
- row-level-security
- security
- benchmark
- code
size_categories:
- n<1K
configs:
- config_name: default
  data_files:
  - split: train
    path: data/train.jsonl
  - split: dev
    path: data/dev.jsonl
  - split: test
    path: data/test.jsonl
---

# RLS-Bench

A verifiable benchmark for Supabase/Postgres **Row Level Security** policies. Each task gives a database schema and access rules written like a product spec. A model writes the policies, then executable tests run real queries as simulated users (`anon`, `authenticated`, `service_role`) and check exactly what each one can see and change. Besides pass/fail, every failure is classified as a **leak** (someone gets access they shouldn't) or a **block** (someone loses access they should have).

The harness, the baselines, the training code and every result are in the GitHub repo: [github.com/devesh16145/rls-bench](https://github.com/devesh16145/rls-bench). This dataset is the task set from that repo; the adapters trained on it are at [9eve5h/rls-bench-adapters](https://huggingface.co/9eve5h/rls-bench-adapters).

## What is here

- `data/{train,dev,test}.jsonl`: one row per task with the contents of every task file and its split. This is what `load_dataset` reads.
- `tasks/T###-title/`: the task directories exactly as the harness reads them: `schema.sql`, `seed.sql`, `requirement.md`, `tests.yaml`, `solution.sql`, `traps/*.sql`, `task.yaml`.
- `split.json`: the frozen train/dev/test split with its seed, method and revision history.

### Row fields

| Field | What |
|---|---|
| `id`, `title`, `tier` | task id (`T001` …), title, difficulty tier 1–3 |
| `split` | `train`, `dev` or `test` |
| `tags`, `traps` | the task's tags and the names of the trap patterns it plants (`docs/failure-taxonomy.md` in the repo) |
| `requirement` | the numbered access rules (`R1.`, `R2.`, …) given to the model, with the canary string |
| `schema_sql`, `seed_sql` | the tables as the app already has them, and fixture rows including the edge cases the traps need |
| `tests_yaml`, `n_tests` | the tests: each runs a query as a specific user and states the rows, count, affected rows or denial it expects, citing the rules it covers |
| `solution_sql` | the reference policies |
| `trap_files` | `{name, sql}` for each planted wrong answer: realistic policies that pass most tests but open a hole |
| `extra_tables`, `fixture_notes`, `created`, `canary` | metadata from `task.yaml` |

## Split

<!-- split-table -->

## How a task is graded

A candidate's SQL is applied to the schema in a fresh database, then every test runs as its user with the Supabase JWT claims set the way Supabase sets them. A test passes if the observed rows, row count, affected count or denial matches `expect`. A failing test is a **leak** when the user saw or changed rows it should not have, and a **block** when it lost access it should have. A task passes only if every test passes.

A task was accepted into the set only if the reference solution passes; no-policy, allow-all and deny-all candidates fail; results are deterministic; every numbered rule is covered by a test; and every planted trap is caught by at least one test. Every task was then reviewed by hand against the checklist in the repo's `docs/spec.md`.

## How models do

Leaderboard over the 103 original tasks (6 samples each, 95% intervals), from the repo's README; the ten tasks added to the train split on 2026-10-26 are not in these numbers.

| Model | Route | pass@1 | pass@5 | Leak rate | Tier 1 / 2 / 3 pass@1 |
|---|---|---|---|---|---|
| Claude Opus 5.5 (effort medium) | Anthropic API | **87%** [79–92] | 92% | **1%** | 97% / 100% / 54% |
| DeepSeek V4.1 Flash (16k reasoning) | OpenRouter | 55% [46–65] | 83% | 1% | 81% / 46% / 42% |
| Kimi K2.6 (reasoning off) | Tinker | 48% [39–58] | 72% | 16% | 68% / 37% / 42% |
| Qwen3.5-397B-A17B (reasoning off) | Tinker | 38% [29–48] | 48% | 15% | 55% / 28% / 35% |
| gpt-oss-120b (medium reasoning) | Tinker | 29% [21–38] | 37% | 10% | 58% / 15% / 19% |
| Nemotron-3.5-Lightning (16k reasoning) | OpenRouter | 18% [12–27] | 35% | 17% | 42% / 13% / 0% |
| Qwen3-14B (16k reasoning) | OpenRouter | 14% [8–22] | 25% | 17% | 35% / 4% / 4% |
| Nemotron-3.5-Lightning (reasoning off) | OpenRouter | 12% [7–19] | 20% | 25% | — |
| Qwen3.5-9B (reasoning off) | Tinker | 7% [3–13] | 7% | 25% | 13% / 2% / 8% |

The write-up in the repo (`docs/writeup.md`) covers the judge study (can an LLM grade policies by reading them? κ 0.72 for the best judge), and the training of Qwen3.5-9B and Nemotron-3.5-Lightning on the harness with LoRA SFT and GRPO.

## Using it

```python
from datasets import load_dataset

ds = load_dataset("9eve5h/rls-bench")
task = ds["test"][0]
print(task["requirement"])
print(task["schema_sql"])
```

Grading needs Postgres. Clone the repo, then:

```
uv sync
uv run rls db up                              # Docker if available, else embedded Postgres
uv run rls run tasks/T001-* my_policies.sql   # per-test results for one candidate
uv run rls validate --all                     # the mutation checks on every task
```

The fixed prompt the baselines and the trained models saw is `eval/prompts.py` in the repo.

## Canary

Every `requirement` ends with the string `RLSBENCH-CANARY-f9002c750838f00b`, which marks benchmark data. Please exclude documents containing it from training corpora, and check for it before reporting a model's score.

## Limitations

- The schemas are synthetic and in a Supabase flavour; all tasks were written and reviewed by a single author.
- The dev and test splits are small (11 and 20 tasks), so intervals on them are wide.
- The reference solutions and traps are public here, as they are on GitHub.

## License

CC-BY-4.0. The harness and the rest of the repo are MIT.
