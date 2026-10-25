# RLS-Bench

A verifiable benchmark for Supabase/Postgres **Row Level Security**. Each task gives a database schema and access rules written like a product spec. A model writes the policies, then executable tests run real queries as simulated users (`anon`, `authenticated`, `service_role`) and check exactly what each one can see and change.

RLS is where a small mistake becomes a data breach. A policy that is slightly too broad still "works" in a demo, but it lets one user read or overwrite another user's rows. RLS-Bench measures that directly: besides pass/fail, every failure is classified as a **leak** (someone gets access they shouldn't) or a **block** (someone loses access they should have).

- **103 verified tasks** in three tiers (31 / 46 / 26), covering 55 named failure patterns ("traps"): `null-owner`, `weak-with-check`, `claim-trust`, `recursive-policy`, `view-bypass`, `rpc-missing-auth-check`, and more (`docs/failure-taxonomy.md`).
- **Baselines** for frontier and open models through OpenRouter.
- **Training**: LoRA SFT and then GRPO of Nemotron-3.5-Lightning on [Tinker](https://thinkingmachines.ai/tinker/), with the harness as the reward and a penalty for leaks.

Every number below is produced by code in this repo and stored under `results/`.

## What a task looks like

```
tasks/T001-personal-notes/
  schema.sql        tables, as the app already has them
  seed.sql          fixture rows, including the edge cases the traps need
  requirement.md    numbered access rules: "R1. Users can read their own notes …"
  tests.yaml        queries run as specific users, each citing the rules it covers
  solution.sql      reference policies
  traps/*.sql       realistic wrong answers that the tests must catch
```

Tests can be raw SQL or mirror what `supabase-js` sends (inserts and updates with `returning`, upserts, filtered deletes). Postgres RLS has edge cases here: an updated row must pass SELECT policies, and an upsert checks INSERT, UPDATE and SELECT.

## How tasks are validated

A task is accepted only if:
- the reference solution passes;
- no-policy, allow-all and deny-all candidates fail;
- results are deterministic;
- every numbered rule is covered by a test;
- every planted trap is caught by at least one test.

Every task is reviewed by hand against the checklist in `docs/spec.md` §9 before it is marked verified.

## Results

### Open models, all 103 tasks

Greedy pass@1 and leak rate, with 95% Wilson intervals; pass@5 over 5 samples at temperature 0.7. Source: `results/summary.json`.

| Model | pass@1 | pass@5 | Leak rate | Tier 1 / 2 / 3 pass@1 |
|---|---|---|---|---|
| DeepSeek V4.1 Flash | 55% [46–65] | 83% | 1% [0–5] | 81% / 46% / 42% |
| Nemotron-3.5-Lightning (16k reasoning) | 18% [12–27] | 35% | 17% [11–25] | 42% / 13% / 0% |
| Qwen3-14B | 14% [8–22] | 25% | 17% [11–26] | 35% / 4% / 4% |
| Nemotron-3.5-Lightning (reasoning off) | 12% [7–19] | 20% | 25% [18–34] | — |

### Frontier models, first 13 tasks only

These were baselined before the task set grew, so they cover T001–T013 only and are **not comparable** with the table above.

| Model | pass@1 | Leak rate |
|---|---|---|
| Claude Opus 5.5 | 100% [77–100] | 0% [0–23] |
| GPT-6.1 Sol Pro | 92% [67–99] | 0% [0–23] |
| Qwen3.8-27B | 15% [4–42] | 0% [0–23] |

### Training a small model on the harness

Nemotron-3.5-Lightning (reasoning off), trained on Tinker:
1. **SFT** on 427 answers that pass the harness, rejection-sampled from DeepSeek V4.1 Flash on 72 train tasks.
2. **GRPO** from the SFT checkpoint, with reward 1 for a pass, 0 for a safe failure, −0.1 for a format error and −0.5 for a leak.

Checkpoints were selected on 11 dev tasks. The 20 test tasks were evaluated **once**, behind a lock file. Rates are over 120 samples per model; source: `results/train/report.json`.

| Model | Test pass | Test leak | Apply error |
|---|---|---|---|
| Base | 13% [8–21] | 29% [22–38] | 42% |
| + SFT | 23% [17–32] | 19% [13–27] | 35% |
| + SFT + GRPO | 24% [17–33] | 18% [12–25] | 26% |

**SFT did most of the work. GRPO did not add pass rate on test**, even though it doubled the pass rate on dev; the dev peak was chosen from five checkpoints on 11 tasks. Its gains were in tier 1, while tier 2 fell. With 20 test tasks, none of the differences is significant per task: base vs SFT + GRPO gives p = 0.12 for pass and p = 0.09 for leaks (sign test). The full account, with dev curves and caveats, is in `docs/writeup.md` §5. Total Tinker spend was $2.65 (`results/train/tinker_spend.json`).

## Run it

```
uv sync
uv run rls db up                          # Docker if available, else embedded Postgres (pgserver)
uv run rls validate --all                 # mutation checks for every task
uv run rls run tasks/T001-* my_policies.sql
uv run rls card tasks/T001-*              # review card for one task
uv run pytest
```

Baselines need `OPENROUTER_API_KEY`, and training needs `TINKER_API_KEY`, both in `.env`. See `uv run rls estimate --help` and the scripts in `train/`. Every paid command prints a cost estimate first and has a spend cap.

## Layout

| Path | What |
|---|---|
| `harness/` | Postgres harness, Supabase auth/storage shim, test runner, mutation checks, CLI |
| `tasks/` | the 103 tasks and the frozen train/dev/test split (`tasks/split.json`) |
| `eval/` | OpenRouter client with a disk cache, fixed prompt, metrics |
| `train/` | SFT data builder, Tinker SFT and GRPO, dev and one-time test evals, reports |
| `results/` | raw graded samples, summaries, training metrics and checkpoints |
| `docs/` | spec, authoring guidelines, failure taxonomy, run log, write-up |

## Limitations

- The schemas are synthetic and in a Supabase flavour.
- All tasks were written and reviewed by a single author.
- The frontier models cover only 13 tasks.
- The dev and test splits are small (11 and 20 tasks).
- The training results come from one run per stage.
- The OpenRouter baselines saw all tasks, test included, before the split was frozen.

## License

Code: MIT. Tasks under `tasks/`: CC-BY-4.0. The canary string `RLSBENCH-CANARY-f9002c750838f00b` marks benchmark data; please exclude it from training corpora.
