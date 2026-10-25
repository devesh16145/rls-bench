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

### Leaderboard, all 103 tasks

Greedy pass@1 and leak rate with 95% Wilson intervals; pass@5 over 5 samples at temperature 0.7. Reasoning is each model's default where the route allows it; "reasoning off" rows use the model's no-thinking template with a 4,096-token cap. Source: `results/leaderboard.json`; figure: `results/figures/leaderboard.png`.

| Model | Route | pass@1 | pass@5 | Leak rate | Tier 1 / 2 / 3 pass@1 |
|---|---|---|---|---|---|
| Claude Opus 5.5 (effort medium) | Anthropic API | **87%** [79–92] | 92% | **1%** | 97% / 100% / 54% |
| DeepSeek V4.1 Flash (16k reasoning) | OpenRouter | 55% [46–65] | 83% | 1% | 81% / 46% / 42% |
| Kimi K2.6 (reasoning off) | Tinker | 48% [39–58] | 72% | 16% | 68% / 37% / 42% |
| gpt-oss-120b (medium reasoning) | Tinker | 29% [21–38] | 37% | 10% | 58% / 15% / 19% |
| Nemotron-3.5-Lightning (16k reasoning) | OpenRouter | 18% [12–27] | 35% | 17% | 42% / 13% / 0% |
| Qwen3-14B (16k reasoning) | OpenRouter | 14% [8–22] | 25% | 17% | 35% / 4% / 4% |
| Nemotron-3.5-Lightning (reasoning off) | OpenRouter | 12% [7–19] | 20% | 25% | — |
| Qwen3.5-9B (reasoning off) | Tinker | 7% [3–13] | 7% | 25% | 13% / 2% / 8% |

The frontier model fails closed: of Opus's 13 misses, 11 deny a legitimate user, one is SQL that failed to apply, and one leaks. The small open models leak on 17–25% of tasks. Everyone's failures concentrate in tier 3, where the logic lives in security-definer RPCs and approval workflows. GPT-6.1 Sol Pro was run on the first 13 tasks only (92% pass@1) before the set grew; it is not in the table.

### Can a judge replace the harness?

Judges read the rules, the schema and a candidate's SQL (never the tests) and label it pass / leak / block / error; the harness provides the truth. On 400 held-out candidates from the test tasks (100 per label), source `results/judge/summary.json`:

| Judge | κ vs harness | Leak recall | Leak precision | Leaks called "pass" |
|---|---|---|---|---|
| Claude Opus 5.5 | **0.72** | **97%** | 67% | 2% |
| Qwen3-8B fine-tuned on 2,352 harness-labelled candidates | 0.48 | 53% | 62% | 10% |
| gpt-oss-120b, reasoning | 0.36 | 82% | 42% | 0% |
| Kimi K2.6, thinking on / off | 0.16 / 0.16 | 59% / 34% | 35% / 24% | 6% / 1% |

Even the best judge agrees with the database four times in five; the confusion is between "too strict" and "too loose", which reading a policy cannot settle. Details in `docs/writeup.md` §4.

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
- Leaderboard rows mix three serving routes; the same model served two ways scored differently on the same tasks.
- The dev and test splits are small (11 and 20 tasks).
- The training results come from one run per stage.
- The OpenRouter baselines saw all tasks, test included, before the split was frozen.

## License

Code: MIT. Tasks under `tasks/`: CC-BY-4.0. The canary string `RLSBENCH-CANARY-f9002c750838f00b` marks benchmark data; please exclude it from training corpora.
