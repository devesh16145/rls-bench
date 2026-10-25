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

Nine models were run on all 103 tasks with the fixed prompt and protocol. Qwen3.5-9B, Qwen3.5-397B, Kimi K2.6 and gpt-oss-120b were sampled on Tinker with their reasoning templates off (gpt-oss has none; it ran at its medium default) and a 4,096-token cap; DeepSeek V4.1 Flash, Qwen3-14B and Nemotron-3.5-Lightning through OpenRouter at their default reasoning with a 16,000-token cap; Claude Opus 5.5 through the Anthropic API at its default effort with an 8,000-token cap. Numbers are from `results/leaderboard.json`; intervals are 95% Wilson.

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

Can the benchmark's own grader train a small open model to write safer policies? Two students were trained on Tinker: Qwen3.5-9B (the main one; the cookbook has a calibrated learning rate for it) and Nemotron-3.5-Lightning (30B total, 3B active). Each went through LoRA SFT on answers that pass the harness, then GRPO with the harness as the reward. Every number below comes from records under `results/`; rates are over all samples with 95% Wilson intervals unless stated otherwise. Dev is 11 tasks × 6 samples (66), test 20 × 6 (120).

### 5.1 Version 1, and why it was redone

The first attempt (Nemotron only) used a hand-written RL loop: 25 steps of 64 rollouts, 1,600 answers in total, an untuned learning rate, no training-health metrics. On test it gave base 13% pass / 29% leak, SFT 23% / 19%, SFT+RL 24% / 18%: SFT did the work and RL added nothing measurable. That is what a token-sized RL run looks like, not a finding about RL. Version 2 keeps the data and the split, and redoes training on the cookbook's loops at a scale where the curves mean something.

### 5.2 Split and SFT data

The 103 tasks were split once, stratified by tier with a fixed seed: 72 train, 11 dev, 20 test. SFT data was built by rejection sampling: DeepSeek V4.1 Flash answered each train task 16 times at temperature 0.8, the harness graded every answer, and up to 6 distinct passing answers per task were kept, plus the reference solution.

| Tier | Tasks | Samples | Passed | Cut off at 16k tokens | Training examples |
|---|---|---|---|---|---|
| 1 | 22 | 352 | 293 (83%) | 10 | 145 |
| 2 | 32 | 512 | 278 (54%) | 198 | 191 |
| 3 | 18 | 288 | 111 (39%) | 87 | 91 |
| **All** | **72** | **1,152** | **682 (59%)** | **295** | **427** |

Two tier-3 tasks had no passing sample and contribute only their reference. A held-out loss set of 57 examples (the 11 dev references plus 46 passing DeepSeek answers on dev tasks) was used to pick learning rates. Sampling cost $6.45 on OpenRouter.

### 5.3 SFT, with a learning-rate sweep

Rank-32 LoRA, 3 epochs, batch 16 (78 steps), linear decay, loss on the answer only, dev loss every 10 steps. Three learning rates per student; the lowest final dev loss wins and that run *is* the SFT model, so nothing is retrained.

| Student | Learning rates | Final dev loss | Chosen | Dev pass / leak (the chosen model) |
|---|---|---|---|---|
| Qwen3.5-9B | 1.58e-4 / 4.73e-4 / 1.42e-3 | 0.145 / **0.141** / 0.147 | 4.73e-4 (the cookbook's calibrated rate) | 24% / 26% |
| Nemotron-3.5-Lightning | 3e-5 / 1e-4 / 3e-4 | 0.205 / 0.159 / **0.153** | 3e-4 | 30% / 44% |

Dev reference points for the untrained students: Qwen3.5-9B 0% pass / 12% leak (59% of its answers fail to apply); Nemotron 9% / 39%. For Nemotron, the version-1 SFT at 1e-4 scored 15% pass on the same dev samples; tuning the learning rate alone doubled it. Each sweep run cost about $2.40 (Qwen) or $0.76 (Nemotron).

### 5.4 GRPO on the cookbook loop

**Environment.** The harness is wrapped as a cookbook RL environment: an episode is the fixed prompt for a train task, the model's answer, and the harness grade as the reward: 1 for a pass, 0 for a safe failure (a block, or SQL that fails to apply), −0.1 for a format error, and **−0.5 for a leak**, so that a group of answers that all fail still prefers failing closed. All 72 references score 1 through the environment; of the 200 trap files, 180 score −0.5 and 20 score 0, none 1.

**Loop.** The cookbook's RL loop with group-centred rewards (8 answers per task, temperature 1.0), constant-reward groups dropped, the importance-sampling loss, no KL penalty, 2,048-token answers, 16 tasks per step. Sampler-vs-trainer KL and entropy are logged every step; dev is evaluated and a checkpoint saved every 10 steps; the checkpoint with the highest dev pass rate is kept.

**Learning-rate sweeps (10 steps each).** Qwen3.5-9B: 2e-5 learned slowly but stably; 6e-5 learned fastest (train pass 41% → 54%) but its entropy fell from 0.08 to 0.02 in ten steps; 2e-4 collapsed (reward 0.30 → 0.12). The full run uses 4e-5. Nemotron: 6e-5 beat 2e-5 (reward 0.29 → 0.36 vs flat) with stable KL; the full run uses 6e-5. All three Qwen sweep runs raised the dev leak rate above the SFT model's while cutting dev apply errors: SQL that used to fail to apply now applied and leaked, mostly on two tasks.

**Full runs (50 steps × 16 tasks × 8 rollouts, 6,400 rollouts, about 11 passes over the train tasks).**

| Run | Train reward | Train pass | Train leak | Answer length | Entropy | Cost |
|---|---|---|---|---|---|---|
| Qwen3.5-9B, seed 0 | 0.34 → 0.63 | 44% → 65% | 18% → 2.6% | 664 → 907 | 0.068 → 0.015 | $15.77 |
| Qwen3.5-9B, seed 1 | 0.31 → 0.50 | 41% → 53% | 21% → 6% | 638 → 918 | 0.073 → 0.022 | $15.98 |
| Nemotron, lr 6e-5 | 0.33 → 0.49 | 43% → 53% | 20% → 7% | 620 → 832 | 0.072 → 0.017 | $5.64 |

(First five steps → last five. Sampler–trainer KL stayed below 6e-4 for Qwen and 5e-3 for Nemotron.)

### 5.5 Dev during training

| Checkpoint | Qwen seed 0, pass / leak | Qwen seed 1 | Nemotron |
|---|---|---|---|
| SFT (step 0) | 24% / 26% | 24% / 26% | 30% / 44% |
| step 10 | 21% / 38% | 21% / 32% | 27% / 49% |
| step 20 | 29% / 39% | 26% / 32% | 29% / 42% |
| step 30 | 45% / 18% | 32% / 20% | 27% / 36% |
| step 40 | **52% / 6%** | **53% / 21%** | 23% / 23% |
| step 50 | 47% / 18% | 38% / 35% | **38% / 17%** |

Both Qwen seeds peak at step 40 and fall back by step 50 while train reward keeps rising: the last ten steps look like the start of overfitting to 72 tasks. Nemotron's leak rate fell at every evaluation; its pass rate moved within noise until the last one. Greedy pass@1 on the 11 dev tasks went from 2 to 5 for Qwen (both seeds) and from 3 to 4 for Nemotron. Figures: `results/figures/dev_curve_*.png`, `results/figures/rl_health_*.png`.

### 5.6 Repair: a second and third try with harness feedback

The same environment with up to three turns: a failing answer gets back the names of the failing tests, the rules they cover, whether each failure was a leak or a block, and the SQL error if any; never the expected rows or the test queries. The model then rewrites the whole answer. Turns after the first cost 0.05.

First, the protocol alone, on dev (pass after 1 / 2 / 3 tries): base 0% / 9% / 12%; SFT 23% / 30% / 36%; GRPO step 40 **52% / 62% / 67%**. Feedback is worth 10–15 points to every model, in proportion to what it can already do.

Then training on it: 25 steps × 16 tasks × 4 rollouts from the GRPO step-40 checkpoint, 1,536-token answers, $8.07. Train reward stayed flat (0.59 → 0.57), first-try pass fell from 42% to 38% and tries per episode rose from 1.8 to 1.9; on dev the third-try pass rate went 67% → 65% → 55% → 58% → 58% across the five checkpoints. The model had already collapsed to near-deterministic sampling in the GRPO run (entropy 0.011 at the start of repair training), which leaves GRPO little to work with. The pre-registered repair checkpoint is step 5, which is indistinguishable from the GRPO model it started from. Figure: `results/figures/repair.png`.

### 5.7 Pure distillation

_Pending: the on-policy distillation run (Qwen3.5-9B from Qwen3.5-397B, environment reward off) is in progress; its dev results and the SFT / GRPO / distillation comparison go here._

### 5.8 Test (evaluated once for version 2)

_Pending: the pre-registered test evaluation (`docs/preregistration.md`) runs after the distillation row is chosen._

### 5.9 Cost

_Pending: final Tinker spend by stage from `results/train/tinker_spend.json`._

### 5.10 Caveats specific to training

- 72 train tasks is small for RL: 50 steps cycle through them eleven times, and both Qwen seeds show the dev peak-then-fall pattern of a policy starting to memorise them.
- Entropy collapses to near zero in every GRPO run. Pass rate kept improving on dev until step 40, but a near-deterministic policy at temperature 1 has little left to explore, and the repair run showed what that costs.
- The dev set is 11 tasks: one task is 9 points of greedy pass@1 and 6 samples are 9 points of the all-sample rate. Checkpoint choice is noisy; the test split is what the claims rest on.
- Answers got about 40% longer under GRPO. Longer is not better or worse in itself here (the cap was not reached), but it is the kind of drift a reward with no length term allows.
- The leak penalty is not symmetric with the pass reward, and tasks that always fail still train the policy to fail closed; on dev this showed up as apply errors turning into leaks early in training before the leak rate fell.

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
