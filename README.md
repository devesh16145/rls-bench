# RLS-Bench

A verifiable benchmark for Supabase/Postgres **Row Level Security**. Each task gives a database schema and access rules written like a product spec. A model writes the policies, then executable tests run real queries as simulated users (`anon`, `authenticated`, `service_role`) and check exactly what each one can see and change.

RLS is where a small mistake becomes a data breach. A policy that is slightly too broad still "works" in a demo, but it lets one user read or overwrite another user's rows. RLS-Bench measures that directly: besides pass/fail, every failure is classified as a **leak** (someone gets access they shouldn't) or a **block** (someone loses access they should have).

- **113 verified tasks** in three tiers (31 / 52 / 30): 103 in the frozen split, plus 10 appended to the train split on 2026-10-26 (every leaderboard and test number below is on the original 103), covering 61 named failure patterns ("traps"): `null-owner`, `weak-with-check`, `claim-trust`, `recursive-policy`, `view-bypass`, `rpc-missing-auth-check`, and more (`docs/failure-taxonomy.md`).
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
| Qwen3.5-397B-A17B (reasoning off) | Tinker | 38% [29–48] | 48% | 15% | 55% / 28% / 35% |
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

Two students were trained on [Tinker](https://thinkingmachines.ai/tinker/) with the harness as the signal: Qwen3.5-9B and Nemotron-3.5-Lightning (30B, 3B active), both with their reasoning templates off.

1. **SFT** on 427 answers that pass the harness (rejection-sampled from DeepSeek V4.1 Flash on the 72 train tasks), with a learning-rate sweep judged on held-out dev loss.
2. **GRPO** on the cookbook's RL loop, the harness grading every rollout: 1 for a pass, 0 for a safe failure, −0.1 for a format error, −0.5 for a leak. Learning-rate sweeps first, then 50 steps × 16 tasks × 8 rollouts; two seeds for Qwen.
3. **Repair RL**: up to three tries, with the failing tests and SQL errors fed back (never the expected rows).
4. **Pure distillation** from Qwen3.5-397B as a third route from the base model, for comparison.

Checkpoints were chosen on the 11 dev tasks; the 20 test tasks were evaluated once, pre-registered in `docs/preregistration.md` and locked to a commit. Pass and leak rates over 120 test samples (20 tasks × 6), 95% intervals; source `results/test_eval_v2/summary.json`, figure `results/figures/methods_test.png`.

| Row | Test pass | Test leak |
|---|---|---|
| Qwen3.5-9B base | 9% [5–16] | 18% |
| + SFT | **38%** [29–46] | 16% |
| + SFT + GRPO, seed 0 | 38% [30–47] | 29% |
| + SFT + GRPO, seed 1 | **41%** [32–50] | **14%** |
| + repair-trained | 41% [32–50] | 18% |
| distillation only | 31% [23–40] | 18% |
| SFT on two-source data (v3) | 33% [26–42] | 31% |
| + GRPO, seed 0 (v3) | **45%** [36–54] | 25% |
| + GRPO, seed 1 (v3, 30 steps) | 36% [28–45] | 17% |
| SFT on 82 train tasks (v4, ten new tasks) | 35% [27–44] | 15% |
| + GRPO at half batch (v5, step 10 of 40) | 27% [20–35] | 24% |
| Nemotron base | 12% [7–19] | 22% |
| + SFT | 26% [19–34] | 31% |
| + SFT + GRPO | 29% [22–38] | **10%** |

What held up: a tuned SFT is most of the gain (9% → 38%); Nemotron's GRPO cut its leak rate on 13 of 20 test tasks (31% → 10%, the one significant paired result); and harness feedback is the most reliable lever of all, taking the GRPO model from 35% to 63% within three tries. What did not: GRPO's dev gain for Qwen (24% → 52%) did not transfer to test (38% → 38–41%), and the two seeds disagree on the leak rate by 15 points, so at this scale run-to-run variance is as large as the effect. A third version changed only the SFT data (answers from two open models instead of one): the pass rate stayed put and the leak rate doubled (16% → 31%), because the second model's leakier style carried over; GRPO on it produced the highest pass rate of any row (45%) while pulling leaks back to 25%. Ten more train tasks then repaired the leak rate for SFT alone (31% → 15%, lower on 7 of 8 differing tasks) without moving the pass rate. GRPO on that model at half the batch size, the last of the credit, made it worse (35% → 27% pass, 15% → 24% leak, worse on 5 of the 6 tasks that differ), with the dev curve falling from step 10 on: the version-3 GRPO gain did not survive a smaller run. Every run's curves, dev evaluations and the training-health metrics are under `results/train/`; the full account, including the reward-hacking checks, is `docs/writeup.md` §5. The trained adapters are exported in Hugging Face format (`results/train/adapter_manifest_*.json`). Tinker spend for the whole project: $145.94 (`results/train/tinker_spend.json`).

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
| `tasks/` | the 113 tasks and the train/dev/test split (`tasks/split.json`, frozen for dev and test; train revisions recorded in the file) |
| `eval/` | OpenRouter client with a disk cache, fixed prompt, metrics |
| `train/` | SFT data builder, Tinker SFT and GRPO, dev and one-time test evals, reports |
| `results/` | raw graded samples, summaries, training metrics and checkpoints |
| `docs/` | spec, authoring guidelines, failure taxonomy, run log, write-up |

## Limitations

- The schemas are synthetic and in a Supabase flavour.
- All tasks were written and reviewed by a single author.
- Leaderboard rows mix three serving routes; the same model served two ways scored differently on the same tasks.
- The dev and test splits are small (11 and 20 tasks); the test split was evaluated five times (once per version of the write-up, the last two single rows), with no training decision informed by it.
- The training results come from one or two runs per stage; two seeds of the same GRPO recipe differ by 15 points of leak rate on test.
- The OpenRouter baselines saw all tasks, test included, before the split was frozen.

## License

Code: MIT. Tasks under `tasks/`: CC-BY-4.0. The canary string `RLSBENCH-CANARY-f9002c750838f00b` marks benchmark data; please exclude it from training corpora.
