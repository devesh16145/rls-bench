# RLS-Bench: write-up (draft)

Outline from `docs/spec.md` §11. Only the training section is drafted; the other sections are not yet written.

1. Why RLS (below)
2. Benchmark design (below)
3. Results (below)
4. Judge calibration (below)
5. Training a small model on the harness (below)
6. Limitations (below)
7. What's next (below)

---

## 1. Why Row Level Security

Supabase apps talk to Postgres directly from the browser. There is no application server in between to decide who may read which row; that decision is made by Row Level Security policies on the tables themselves, evaluated by the database for every query under the caller's identity. When the policies are right, a user can only see and change what the product rules allow. When they are slightly wrong, the app still works in every demo and every happy-path test, and someone else's rows are one filtered `select` away.

Two things make this a good benchmark for code-writing models. First, correctness is executable: a policy set either lets the wrong user through or it does not, and the database can be asked. There is no need for a judge model to guess whether SQL is "secure". Second, the mistakes are specific and repeatable. A policy that forgets `with check` on an update, one that trusts a claim the client controls, one that lets the owner column be rewritten, a view that runs with its owner's rights: each is a small, named pattern that shows up again and again, in human code and in model output. That makes it possible to measure not just how often a model fails but how.

The benchmark asks a direct question: given a schema and the access rules written as a product manager would write them, can a model write the policies, and when it cannot, does it fail safe or fail open?

## 2. Benchmark design

**Tasks.** Each of the 103 tasks is a small application: a schema (`schema.sql`), fixture rows (`seed.sql`), the access rules as numbered requirements (`requirement.md`, "R1. Users can read their own notes…"), a reference solution, and a test file. Tasks come in three tiers: single-owner tables and public/private rows (tier 1), memberships, roles, state transitions and time windows (tier 2), and security-definer helpers, RPCs, storage paths and multi-tenant claims (tier 3). Every task also lists the trap patterns it is built to catch, drawn from a taxonomy of 61 named failure modes (`docs/failure-taxonomy.md`), 55 of which appear in the tasks.

**Tests.** A test is a query run as a specific caller: `anon`, an authenticated user with chosen JWT claims, or `service_role`. It states what should happen: these rows, this count, this many rows affected, an error, or a denial. Tests can be raw SQL or mirror what the `supabase-js` client sends (inserts and updates with `returning`, upserts with `on conflict`, filtered deletes), because Postgres treats those differently: an updated row must still satisfy the `select` policy, an upsert checks the insert, update and select policies together, and a delete needs the row to be visible. Each test cites the rules it covers, and every rule must be covered.

**Grading.** A candidate's SQL is applied to a fresh clone of the task database; then each test runs in its own transaction with the caller's role and claims set, and is rolled back. Besides pass or fail, every failure is classified: a **leak** when a caller got access the rules forbid, a **block** when a caller lost access the rules allow. A candidate whose SQL fails to apply, or that produces no SQL block, is recorded as such. The leak rate is the headline number, because a blocked user files a bug and a leaked row does not.

**What makes a task valid.** A task is accepted only when the reference passes; the no-policy, allow-all and deny-all candidates all fail; results are identical across runs; every rule has a test; and every trap the task claims to catch is caught: for each trap there is a realistic wrong answer under `traps/`, and at least one test must fail on it. Several traps turned out to be caught by accident the first time (a leaky update policy rejected by the select policy, for instance); those tests were tightened until the trap failed for the right reason. Tests were never weakened to make a reference pass.

**Prompt and protocol.** Models see one fixed prompt: a short system instruction, the schema, the row counts of the fixture (never the rows), and the requirements verbatim. Zero-shot, no tools, no retries. Each model is sampled once greedily and five times at temperature 0.7 per task, which gives pass@1 and pass@5. Every rate is reported with a 95% Wilson interval. Models whose API ignores temperature are recorded as such.

**Split.** The tasks were split once, stratified by tier with a fixed seed, into 72 train, 11 dev and 20 test. Training data comes from train tasks only; checkpoints are chosen on dev; the test split is evaluated once per version of this write-up and the evaluation is locked to a git commit.

## 3. How models do on the benchmark

Nine models were run on all 103 tasks with the fixed prompt and protocol. The small open models and Kimi K2.6 were sampled on Tinker with their reasoning templates off and a 4,096-token cap; DeepSeek V4.1 Flash, Qwen3-14B and Nemotron-3.5-Lightning through OpenRouter at their default reasoning with a 16,000-token cap; Claude Opus 5.5 through the Anthropic API at its default effort with an 8,000-token cap. Numbers are from `results/leaderboard.json`; intervals are 95% Wilson.

| Model | Greedy pass@1 | pass@5 | Leak rate | Pass by tier 1 / 2 / 3 |
|---|---|---|---|---|
| Claude Opus 5.5 (effort medium) | **87%** [79, 92] | 92% | **1%** | 97% / 100% / 54% |
| DeepSeek V4.1 Flash (16k reasoning) | 55% [46, 65] | 83% | 1% | 81% / 46% / 42% |
| Kimi K2.6 (thinking off) | 48% [39, 58] | 72% | 16% | 68% / 37% / 42% |
| Qwen3.5-397B-A17B (thinking off) | 38% [29, 48] | 48% | 15% | 55% / 28% / 35% |
| gpt-oss-120b (medium reasoning) | 29% [21, 38] | 37% | 10% | 58% / 15% / 19% |
| Nemotron-3.5-Lightning (16k reasoning) | 18% [12, 27] | 35% | 17% | 42% / 13% / 0% |
| Qwen3-14B (16k reasoning) | 14% [8, 22] | 25% | 17% | 35% / 4% / 4% |
| Nemotron-3.5-Lightning (reasoning off) | 12% [7, 19] | 20% | 25% | — |
| Qwen3.5-9B (reasoning off) | 7% [3, 13] | 7% | 25% | 13% / 2% / 8% |

**The frontier model fails closed; small models fail open.** Opus misses 13 of 103 tasks and leaks on one (T072, an escrow state machine); eleven of the other twelve are blocks, where a legitimate user is denied, and one (T021) is SQL that failed to apply. The small open models leak on 17–25% of tasks, as often as or more often than they pass. For a security property that asymmetry is the whole story: the same pass rate can mean "mostly harmless" or "mostly exposed".

**Tier 3 separates everyone.** Opus is near-perfect on tiers 1 and 2 and at 54% on tier 3. Its failures concentrate on tasks where the policy is not enough and the logic lives in a security-definer RPC: `rpc-input-validation` (0 of 4 tasks), `rpc-missing-auth-check` (3 of 8), `self-approval` (5 of 10), `state-transition` (14 of 19). Ten of its eleven blocks are RPC or approval-workflow tasks (T022, T043, T053, T061, T081, T082, T092, T101, T102, T103); the eleventh is T027 (API keys whose hash column must never be readable). T021 is the only task where its SQL failed to apply.

**Reasoning budgets matter as much as reasoning.** DeepSeek V4.1 Flash passes 55% greedily and 83% with five tries, with a 1% leak rate, but 38% of its greedy answers are format errors: in 37% of samples the 16,000-token budget ran out before the answer, almost all on tier 2–3 tasks. The same model with thinking off cannot be measured on Tinker (sampling is not offered there). gpt-oss-120b has the opposite problem: half of its answers fail to apply at all.

**Where the open models fail.** Kimi K2.6 with thinking off is the strongest open model that answers within budget (48%), and its weakest patterns are the ones that need Postgres semantics rather than reading the rules: `view-bypass` (1 of 5), `old-vs-new` and `aggregate-limit` (2 of 8 each), `restrictive-vs-permissive` (1 of 4), `state-transition` (5 of 19). The per-trap heatmap (`results/figures/trap_heatmap.png`) shows the same shape across models: single-owner and public/private rules are mostly solved; anything where two policies interact, or where the rule compares the row before and after an update, is not.

**Two quoted failures.** *A policy with no audience* (T001, Nemotron-3.5-Lightning): the rules say signed-in users may read public notes but anonymous visitors may not. The answer was

```sql
create policy "Users can read public notes" on public.notes
  for select using (is_public = true);
```

With no `to authenticated`, the policy applies to every role, so the `anon` test that expects a denial gets the two public notes back. Nothing in the SQL looks wrong until it is run as the wrong user.

*A check that cannot fail* (T009, Kimi K2.6): a file's owner must never change. The update policy on `files` ends with

```sql
  with check (
    owner_id = files.owner_id  -- prevent owner change
    and public.can_edit_file(files)
  );
```

Inside a `with check`, `files.owner_id` *is* the new row's `owner_id`, so the comparison is always true; the comment says what the author meant, the SQL does something else. An editor can rename a file and set `owner_id` to themselves in the same statement, and `editor_cannot_take_ownership` fails with one row updated. Comparing the old and new row needs a trigger, which is why `old-vs-new` is its own trap in the taxonomy.

## 4. Can a judge replace the harness?

Most evaluation pipelines cannot execute the code they grade; they ask a model to read it. This section measures how well that works for RLS, where the harness gives ground truth.

**Setup.** A judge reads the access rules, the schema and a candidate's SQL, never the tests, and answers one word: `pass`, `leak` (some user gets access the rules forbid), `block` (no leak, but allowed access is denied or a rule is implemented wrongly) or `error` (the SQL would not apply, or there is none). The labels come from the harness. The judge set is 400 candidates from the 20 test tasks, 100 per label, drawn from every graded sample in `results/` and deduplicated on normalised SQL. Four zero-shot judges were compared with one trained judge: Qwen3-8B fine-tuned (LoRA) on 2,352 harness-labelled candidates from train tasks only, with 160 dev-task candidates as the held-out loss. Zero-shot judges that reason were given 1,500–2,000 output tokens; the verdict is the last label word in the answer.

| Judge | Agreement (κ) | Accuracy | Leak recall | Leak precision | Leaks called "pass" | Cost per 400 |
|---|---|---|---|---|---|---|
| Claude Opus 5.5, effort medium | **0.72** | 79% [75, 83] | **97%** | **67%** | 2% | $7.34 |
| Trained Qwen3-8B judge | 0.48 | 61% [56, 66] | 53% | 62% | 10% | $0.09 |
| gpt-oss-120b, reasoning | 0.36 | 52% | 82% | 42% | 0% | $0.53 |
| Kimi K2.6, thinking on | 0.16 | 36% | 59% | 35% | 6% | $4.24 |
| Kimi K2.6, thinking off | 0.16 | 37% | 34% | 24% | 1% | $1.05 |

Chance agreement on a balanced four-way set is κ = 0.

**What the numbers say.**

- *Reading SQL is not the same as running it.* The best judge agrees with the harness 79% of the time. The harness is never wrong about whether a row came back; a judge that is right four times in five would mislabel one candidate in five if it were used as the grader.
- *The confusion is between leak and block, not between safe and unsafe.* Opus gets 97 of 100 leaks and 99 of 100 errors, but only 41 of 100 blocks: it calls a third of blocked answers leaks and a quarter of them passes. Reading a policy, it is hard to tell "too strict" from "too loose" without running a query as the affected user.
- *Reasoning buys recall, not agreement.* Letting Kimi K2.6 think raised its leak recall from 34% to 59% at the same κ; gpt-oss-120b with reasoning catches 82% of leaks but calls 36 of 100 correct answers leaks. For a security reviewer that may be the right trade; for a grader it is not.
- *A small trained judge is competitive and nearly free.* The 8B judge trained on 2,352 examples reaches κ 0.48 with the best leak precision after Opus, at 0.02 cents per judgement. It is also the most dangerous of the useful judges: 10% of real leaks are called "pass".
- *Which leaks get missed.* By the trap pattern of the task (a leak is attributed to every trap its task carries, so these are approximate): the trained judge misses almost every leak involving `recursive-policy`, `sequence-bypass`, `duplicate-approval`, `restrictive-vs-permissive` and `ownership-change` (recall 0–11%), and most `state-transition` leaks (21%), while catching `anon-write-spoof` and `null-owner` (94%). Opus's weakest patterns are the same two Postgres-semantics ones, `recursive-policy` (57%) and `restrictive-vs-permissive` (60%). The misses cluster where the verdict depends on how Postgres combines or evaluates policies, not on what the rule text says.

**Caveats.** The judge set is balanced, so accuracy is not the accuracy you would see on real traffic, where most candidates are errors or blocks. The trained judge's training candidates were produced by the same model families whose test candidates it grades. Opus was run at its default effort; a higher setting might narrow the leak/block confusion.

## 5. Training a small model on the harness

Can the benchmark's own grader train a small open model to write safer RLS? We fine-tuned NVIDIA Nemotron-3.5-Lightning (30B total, 3B active parameters) on Tinker in two stages: LoRA SFT on answers that pass the harness, then GRPO with the harness as the reward. Every number below comes from records in `results/` (paths at the end of the section). Rates are over all samples, with 95% Wilson intervals in brackets unless stated otherwise.

### 5.1 Split

The 103 verified tasks were split once, before any training, stratified by tier with a fixed seed (`tasks/split.json`): 72 train, 11 dev, 20 test. Training data came from train tasks only, and the scripts refuse dev and test tasks. Checkpoints were chosen on dev. The test split was evaluated exactly once, behind a lock file recording the models, the protocol and the git commit.

### 5.2 SFT data: rejection sampling

DeepSeek V4.1 Flash (via OpenRouter) answered each train task 16 times at temperature 0.8, with the benchmark's fixed prompt. The harness graded every answer. Per task, we kept up to 6 distinct passing answers, deduplicated on normalised SQL, plus the reference solution.

| Tier | Tasks | Samples | Passed | Leaked | Cut off at 16k tokens | Training examples |
|---|---|---|---|---|---|---|
| 1 | 22 | 352 | 293 (83%) | 30 | 10 | 145 |
| 2 | 32 | 512 | 278 (54%) | 1 | 198 | 191 |
| 3 | 18 | 288 | 111 (39%) | 9 | 87 | 91 |
| **All** | **72** | **1,152** | **682 (59%)** | **40** | **295** | **427** |

The 427 examples are 355 sampled answers plus 72 references. 50 tasks reached the 6-answer cap. Two tier-3 tasks (T052, T102) had no passing sample and contribute only their reference. Sampling cost $6.45 on OpenRouter.

### 5.3 LoRA SFT

The setup: rank 32, learning rate 1e-4 with linear decay, 3 epochs, batch 16 (78 steps), reasoning-off chat template, and loss on the answer only. Training loss per answer token fell from 0.364 at the first step to 0.134 at the last. The epoch means were 0.251, 0.157 and 0.127. This is training loss only; it shows the model learned the answer format and style, not that it writes correct policies.

### 5.4 GRPO with the harness as reward

**Reward.** 1 if every test passes, 0 for a safe failure (blocked access, or SQL that fails to apply), −0.1 for a format error, and **−0.5 for a leak**. The leak penalty is our addition to the spec's reward. It makes a group of answers that all fail still carry a signal, because failing closed scores above failing open. On the 72 train tasks, all reference solutions score 1. Of the 200 trap mutations, 180 score −0.5 and 20 score 0; none scores 1.

**Task filter.** The SFT model answered each train task 8 times at temperature 1.0. On train it passed 19% of answers and leaked 15%. We dropped tasks whose 8 rewards were identical: T094 (always passed) and T008 (always a safe failure). Of the 70 tasks kept, 39 never passed. They stay in only because their leak and format rewards vary, so most of the signal teaches "fail closed" rather than "pass".

**Training.** We followed the Tinker cookbook's RL loop:
- Rewards centred within each group.
- Groups with identical rewards dropped.
- Importance-sampling loss, no KL penalty.
- Learning rate 4e-5.
- 8 tasks × 8 answers per step, temperature 1.0.
- Answers capped at 2,048 tokens. The spec said 1,024, but 18% of the SFT model's dev answers are longer than that.

Every 5 steps a checkpoint was evaluated on dev, and training stopped after 10 steps without dev improvement. The run stopped at step 25. 174 of 200 groups carried signal. Mean reward per step was noisy, from −0.16 to +0.56, because each step draws different tasks. The mean of the first five steps was +0.11, and of the last five +0.12.

### 5.5 Dev results

Dev has 11 tasks × 6 samples (one greedy, five at temperature 0.7, max 4,096 tokens).

| Checkpoint | Pass | Leak | Greedy pass@1 |
|---|---|---|---|
| Base (Tinker) | 9% [4, 18] | 39% [29, 51] | 1/11 |
| SFT | 15% [8, 26] | 35% [24, 47] | 2/11 |
| GRPO step 5 | 17% [10, 27] | 29% [19, 41] | 2/11 |
| GRPO step 10 | 15% [8, 26] | 24% [16, 36] | 2/11 |
| **GRPO step 15** | **30% [21, 42]** | **21% [13, 33]** | **3/11** |
| GRPO step 20 | 24% [16, 36] | 18% [11, 29] | 2/11 |
| GRPO step 25 | 15% [8, 26] | 18% [11, 29] | 2/11 |

Step 15 was selected. Its gain came from three tasks (T028, T074, T081) that swing between evaluations. Because it is the best of five checkpoints on the same 11 tasks, its dev number is optimistic.

### 5.6 Test results (evaluated once)

Test has 20 tasks × 6 samples = 120 samples per model, with the same protocol as dev.

| Model | Pass | Leak | Apply error | Greedy pass@1 (n = 20) | Greedy leak | Mean answer tokens |
|---|---|---|---|---|---|---|
| Base | 13% [8, 21] | 29% [22, 38] | 42% | 15% [5, 36] | 25% | 848 |
| SFT | 23% [17, 32] | 19% [13, 27] | 35% | 30% [15, 52] | 25% | 678 |
| SFT + GRPO (step 15) | 24% [17, 33] | 18% [12, 25] | 26% | 25% [11, 47] | 35% | 513 |

The 120 samples per model are clustered in 20 tasks, so the sample-level intervals above are too narrow. The fairer test is paired by task. The table counts tasks where the first model did better, then worse, on pass count and on leak count out of 6, with a two-sided sign test:

| Comparison | Pass: better / worse | p | Leak: lower / higher | p |
|---|---|---|---|---|
| SFT vs base | 4 / 2 | 0.69 | 10 / 6 | 0.45 |
| SFT + GRPO vs SFT | 3 / 2 | 1.00 | 7 / 3 | 0.34 |
| SFT + GRPO vs base | 6 / 1 | 0.12 | 10 / 3 | 0.09 |

By tier (pass / leak):

| Tier | Base | SFT | SFT + GRPO |
|---|---|---|---|
| 1 | 42% / 42% | 53% / 14% | 72% / 22% |
| 2 | 2% / 31% | 17% / 17% | 4% / 9% |
| 3 | 0% / 10% | 0% / 30% | 3% / 27% |

### 5.7 What the training did, and did not, show

- **SFT produced most of the change.** Pass rose from 13% to 23%, leak fell from 29% to 19%, and apply errors fell from 42% to 35%.
- **GRPO did not add pass rate on test** (23% → 24%). The dev gain at the selected checkpoint (15% → 30%) did not carry over. That is what you'd expect from picking the best of five evaluations on 11 tasks.
- **GRPO changed behaviour in other ways.** Apply errors fell to 26% and answers got shorter (678 → 513 tokens). On dev the leak rate fell steadily across checkpoints (35% → 18%). On test, the all-sample leak rate barely moved (19% → 18%), while the greedy leak rate rose from 5 to 7 of 20 tasks.
- **GRPO's test gains are in tier 1** (53% → 72%), while tier 2 fell (17% → 4%). The spec lists this pattern ("tier 1 improving while traps don't") as a reward-hacking signal, alongside shrinking answers. We report it rather than explain it away.
- **No difference is significant at the task level.** The strongest is base vs SFT + GRPO: pass p = 0.12, leak p = 0.09. With 20 test tasks, only large effects are detectable.

### 5.8 Cost

Tinker spend, estimated at list prices from recorded token counts, came to $2.65 in total:

| Item | Spend |
|---|---|
| SFT run | $0.66 |
| GRPO filter pass | $0.25 |
| GRPO run, including its five dev evals | $1.51 |
| Smoke run | $0.01 |
| Standalone dev evals | $0.06 |
| Test eval | $0.16 |

The SFT data cost $6.45 on OpenRouter.

### 5.9 Caveats specific to training

- The split is small: 11 dev and 20 test tasks.
- One base model, one seed, one run per stage.
- No tuned learning rate exists for Nemotron in the Tinker cookbook, so both learning rates are recipe defaults (1e-4 for SFT, 4e-5 for GRPO).
- The OpenRouter baselines ran on all 103 tasks, test included, before the split was frozen. No training choice (data, hyperparameters, checkpoint) used test results.
- "Base" in the tables means the base model sampled on Tinker with the same chat template as training. Nemotron served through OpenRouter scored differently on the same dev tasks (reasoning off: 15% pass over all samples), so OpenRouter numbers are not the training baseline.

*Sources: `results/train/sft_data_stats.json`, `results/train/checkpoints.json`, `results/train/sft_*.jsonl`, `results/train/rl_filter_20261025T125454Z.jsonl`, `results/train/rl_*_20261025T133618Z*.jsonl`, `results/tinker_eval/`, `results/test_eval/`, `results/train/report.json` (dev and test tables, tiers and paired sign tests, from `train/report.py`), `results/train/tinker_spend.json` (from `train/spend.py`), `results/train/sft_data_stats.json` (from `train/build_sft.py stats`).*

## 6. Limitations

- **Synthetic schemas, one flavour of Postgres.** Every task was written for this benchmark, in the Supabase dialect (its `auth` and `storage` shims, its default privileges). Real schemas are larger, messier and come with history; a policy that passes here may still be wrong for an app with triggers, views and migrations the task never mentions.
- **One author.** The tasks were written quickly and reviewed against a checklist; the traps and tests reflect one person's sense of what goes wrong. Several traps were only caught for the wrong reason the first time round, and were fixed; others may still be caught for the wrong reason.
- **Small splits.** 11 dev and 20 test tasks. A single task is 9 points of greedy pass@1 on dev and 5 on test, which is why every rate here carries an interval and why differences between trained models are reported with paired tests rather than as point estimates.
- **The test split was looked at twice.** Once for version 1 and once for version 2, with no training decision in between informed by it. Both evaluations are locked to a git commit and recorded.
- **Serving differences.** The leaderboard mixes three routes (OpenRouter, the Anthropic API, Tinker). The same model served two ways scored differently on the same dev tasks (Nemotron: 15% through OpenRouter, 9% through Tinker, both with reasoning off), so rows are comparable within a route more than across.
- **Reasoning budgets confound the ranking.** DeepSeek V4.1 Flash's 16,000-token cap cut off 37% of its answers; a larger budget would raise its score and its cost. Opus ran at its default effort.
- **Contamination.** The tasks are public with a canary string. Models released after October 2026 may have seen them.
- **The judge set is balanced**, so its accuracies are not the accuracies you would see on real traffic, and the trained judge was trained on candidates from the same model families it was tested on.

## 7. What's next

- **More tasks.** The train split is 72 tasks; RL cycles through it eleven times in a 50-step run. A larger train set, and a test set of 40+ tasks, would make both the training and the test numbers much sharper. Tasks are cheap to draft and slow to verify; the review checklist is the bottleneck worth automating partly, with the harness doing the mechanical checks it already does.
- **Judge-in-the-loop training.** The trained judge is cheap enough to grade every rollout; whether a judge-shaped reward reproduces the harness-trained behaviour, or just the judge's blind spots, is a direct test of how much executable grading is worth.
- **A real-schema track.** Policies written against a few open-source Supabase apps, graded by the same harness, would show how much of the benchmark transfers.
- **Longer repair chains with tools.** The repair environment gives the model the failing test names; giving it a `psql` tool to query the database as any user would make the task closer to how a person debugs a policy.
