# Run log

## 2026-10-24 — Phase 1

- `typer==0.12.5` fails with click 8.3 ("Secondary flag is not valid for non-boolean flag"). Fix: pin `click==8.1.7`.
- T001 trap `weak-with-check` (`with check (true)`) initially passed every test. Cause: Postgres checks the updated row against SELECT policies as well, so handing a *private* note to another user fails with 42501 regardless of `with check`. Fix: added test `ana_cannot_hand_public_note_to_ben`, which hands over a public note that stays visible after the update. The test was made stricter, not weaker. Recorded in the taxonomy and authoring guidelines.

## 2026-10-24 — Phase 2 (tasks T004–T010)

- Harness: tests may now contain several statements; the runner advances to the last result (`cur.nextset()`), needed for RPC tests in T010 that call a function and then read the row. No existing test changed result.
- T009: the owner-transfer test is caught by the read policy as well (after a transfer the old owner can no longer see the file), so only `editor_cannot_take_ownership` discriminates the `ownership-change` trap. Kept both; the card records which one catches it.
- The three Phase 1 tasks still read `verified: false` on disk at the start of Phase 2; left unchanged until reviewed.

## 2026-10-24 — first baselines (10 verified tasks)

- Ran `anthropic/claude-opus-5.5` ($2.39) and `openai/gpt-6.1-sol-pro` ($2.01), 60 samples each, max_tokens 16000. Neither model accepts `temperature`; it was not sent (recorded as `temperature_sent: false`).
- Failure: as first graded, both models failed 8 of 10 tasks, every failure in an anon "sees nothing" test. Both models `revoke` table privileges from `anon`, so anon gets 42501 instead of zero rows. Both are correct for "anonymous visitors cannot see anything"; the tests over-specified the mechanism (they expected `rows: [[0]]`, `count: 0` or `affected: 0`).
- Fix: changed those 14 anon tests to `denied` (permission error or zero rows passes; any returned row is still a leak) and `select count(*)` to `select *` so a leak shows as rows. `rls validate --all` still passes, including every trap mutation. Added `tests_hash` to records and `rls regrade`, which re-grades stored completions and appends new records; the original records are kept.
- After regrade: both models pass 10/10 at the first sample and 5/5 sampled at the default temperature. By spec §9.3 (> 90% on Tier 3) the benchmark is too easy; no further tasks until harder designs are agreed.

## 2026-10-24 — supabase-js client tests and harder tasks

- Harness: tests can be written as `client:` calls (insert/update/delete with `returning`, upserts) rendered to the SQL PostgREST runs. Added 32 client tests to T001–T010 citing existing rules; requirements unchanged, so prompts and stored answers are unchanged.
- Regrade on client tests: both models fail `client_admin_upserts_existing_project` (T003) in some samples (GPT at the first sample; Opus in 3 of 5 sampled). Cause: they `revoke all` on `projects` and `grant update (name)`, so an upsert that also sends the unchanged `org_id` gets `permission denied`. Real apps would break, but T003's requirement never says the app uses upsert, so the test arguably goes beyond the requirement. Owner to decide (keep, drop, or add a client sentence to T003 and re-sample).
- T011 reference failed its own bootstrap test. First cause (solution bug): reading back a just-inserted membership row used a helper that queries `org_members`, whose snapshot cannot see the row being inserted. Fix: also allow `user_id = auth.uid()` in the members SELECT policy. Second cause (harness bug): sequences do not roll back, so earlier tests consumed org id 3 and results depended on test order. Fix: the runner resets every public/storage sequence to its post-setup value before each test; `HARNESS_VERSION` bumped to 2 and included in the grading fingerprint so stored answers are regraded. Added a pytest that reversing test order gives identical observations.

## 2026-10-24 — baselines on T011–T013

- Ran both models on T011–T013 (Opus $1.24, GPT $1.13; 18 samples each).
- Failure: GPT failed T013 in 6/6 samples, only on the two "cannot move event to another calendar" tests. Its trigger raised `errcode = 'check_violation'` (SQLSTATE 23514), a correct refusal, but `denied` only accepted 42501 and P0001.
- Fix: `denied` also accepts 23514. Unique (23505) and foreign-key (23503) violations stay excluded because an accidental conflict could mask a hole. `HARNESS_VERSION` → 3; stored answers regraded; `rls validate --all` re-run.

## 2026-10-24 — open-model baselines (13 tasks, max_tokens 16000)

- Ran nvidia/nemotron-3.5-lightning ($0.09), qwen/qwen3-14b ($0.09), qwen/qwen3.8-27b ($2.63), deepseek/deepseek-v4.1-flash-1017 ($0.25). Qwen3-8B is not on OpenRouter; deferred to Tinker sampling.
- Finding: most "format errors" are truncation, not formatting. On OpenRouter reasoning tokens count against max_tokens; samples with finish_reason=length almost always have empty content (reasoning used the whole 16k budget). Truncated samples, all temperatures: Nemotron 35/78, Qwen3-14B 3/78, Qwen3.8-27B 67/78, DeepSeek 27/78. Nemotron also returned finish_reason=error with empty content 5 times.
- Change: `summary.json` now reports `truncation_rate` (greedy) and `truncation_rate_all_samples` per model. Results under the 16k protocol are kept as recorded; no rerun planned.

## 2026-10-25 — reasoning-off baselines

- Added `--reasoning off` (OpenRouter `reasoning: {"enabled": false}`, default cap 4096). Off-runs are stored in `<model>@reasoning-off.jsonl`; a run stops if a fresh off-sample reports reasoning tokens.
- Nemotron-3.5-Lightning, reasoning off: 78/78 samples, $0.01, zero reasoning tokens, one truncation.
- Failure: Qwen3-14B ignored the setting on both OpenRouter providers (NextBit, DeepInfra): the first four samples had 1,175–4,497 reasoning tokens, so the guard stopped the run after 4 samples ($0.002). Raw records kept. Not retried: Qwen3-8B (the actual training candidate) will be sampled through Tinker, where the chat template's thinking switch is under our control.
- `summary.json` now has `tasks_covered` and `complete` per model so partial runs (the 4-sample Qwen3-14B off-run) are visible as such.

## 2026-10-25 — Phase 4 batch 1 (T014–T023)

- Drafted 10 tasks (T014–T016 tier 1, T017–T019 and T023 tier 2, T020–T022 tier 3) with a helper that writes every task file from Python data; each trap file is the reference with one asserted edit.
- T014 `ownership-change` trap and T020's first `privilege-escalation` trap passed every test: in both, the change makes the row invisible under the SELECT policy, and Postgres rejects updates whose new row the user cannot see, so neither was a real hole. T014's trap was dropped; T020's was replaced by an over-broad delete policy (owners deleting, which R4 forbids). Tests unchanged.
- T021 failed the determinism check: `returning *` included `storage.objects.id` (`gen_random_uuid()`). Grading never used those rows. Fix: the determinism fingerprint now compares returned rows only for `rows`/`count` expectations. Removed a filler `app_info` table from T021.

## 2026-10-25 — Phase 4 batch 2 (T024–T033)

- Drafted 10 tasks: T024–T027 tier 1, T028–T030 and T032–T033 tier 2, T031 tier 3 (rebalancing toward the spec's tier mix).
- T024 first `upsert-takeover` trap (`update using (true)`) passed every test: `on conflict do update` also checks the existing row against SELECT policies, so another user's token stayed protected. Replaced with the realistic mistake, a single `for all using (true) with check (user_id = auth.uid())` policy.
- T029 reference failed `host_creates_event`: its events SELECT policy called a security-definer helper that reads `events`, whose snapshot cannot see the row being inserted, so `.insert().select()` failed (same pitfall as T011). Fix in the solution: the policy checks the row's own columns directly. Test unchanged.

## 2026-10-25 — Phase 4 batch 3 (T034–T043)

- Drafted 10 tasks: T034–T036 tier 1, T037–T042 tier 2, T043 tier 3, toward the spec's 30/45/25 mix.
- T035 `null-owner` trap first passed every test: the anonymous-delete test targeted an unapproved entry, which anon cannot see, so the over-broad delete policy had nothing to act on. Added `anon_cannot_delete_approved_anonymous_entry` (stricter, not weaker).
- T043: dropped an "already a member" refusal from the draft before writing tests. A primary-key violation (23505) would also refuse it correctly, but `denied` deliberately does not accept 23505, so the test would have penalised a correct answer.

## 2026-10-25 — Phase 4 batch 4 (T044–T053)

- Drafted 10 tasks: T044–T046 tier 1, T047–T051 tier 2, T052–T053 tier 3.
- T052 `reference-check` trap (document `with check (true)`) first passed every test: the move test sent a document to a folder the editor could not read, so Postgres's rule that updated rows must stay visible blocked it anyway. Gave mia a read grant on HR and pointed the test at moving into a readable-but-not-editable folder; owner's visible grant count updated from 3 to 4.
- T053 deliberately has no unique constraint on `access_approvals(request_id, approver_id)`: with one, a duplicate approval would fail with 23505, which `denied` does not accept, and the trap would be untestable. The function must refuse repeat approvals itself (R4 says so).

## 2026-10-25 — Phase 4 batch 5 (T054–T063)

- Drafted 10 tasks: T054–T056 tier 1, T057–T060 tier 2, T061–T063 tier 3.
- T057 reference failed `provider_sees_own_slots_and_bookings`: my expectation was wrong, not the solution. The provider is also a signed-in patient, so she correctly also sees other providers' open future slots. Scoped the query to her own slots (`where provider_id = ...`), which is what the test checks.
- T059 `time-window` and `reference-check` traps first passed every test: both tests used upsert, and Postgres checks an `on conflict do update` row against the INSERT policy and the SELECT policies, so neither hole was reachable that way. Added plain `update` and `insert` tests (stricter).
- T061: `patient_cannot_dispense` used the patient's own prescription, so the self-dispense check refused it even without the pharmacist check. Pointed it at another patient's prescription so it tests the pharmacist rule directly.

## 2026-10-25 — Phase 4 batch 6 (T064–T073)

- Drafted 10 tasks: T064–T066 tier 1, T067–T071 tier 2, T072–T073 tier 3. Every reference passed and every planted trap was caught on the first validation run; no tests or solutions needed changes in this batch.

## 2026-10-25 — Phase 4 batch 7 (T074–T083)

- Drafted 10 tasks: T074–T076 tier 1, T077–T080 tier 2, T081–T083 tier 3. All references passed and all planted traps were caught on the first validation run; nothing needed changing.
- T075 is the first task whose rule depends on a row's own `created_at` relative to `now()`; its "fresh entry" tests insert and edit in the same test so they stay deterministic.

## 2026-10-25 — Phase 4 batch 8 (T084–T093)

- Drafted 10 tasks: T084–T086 tier 1, T087–T091 tier 2, T092–T093 tier 3.
- T090 `reference-check` trap was caught for the wrong reason: its admin check queried `org_admins` directly, which RLS hides, so it blocked a legitimate admin instead of letting another org's admin in. Replaced with the realistic mistake, a security-definer `is_any_admin()` that ignores the device's organization; now caught by the cross-org tests.
- T092 duplicate-redemption test used the `MAXED` code, so the 5-referral cap refused it even without the "already redeemed" check. Added an unused code (REF-R1) and pointed the test at it.
- At the start of this batch T074–T083 still read `verified: false` on disk; left unchanged until reviewed.

## 2026-10-25 — Phase 4 batch 9 (T094–T103) — task set passes 100

- Drafted 10 tasks: T094–T096 tier 1, T097–T100 tier 2, T101–T103 tier 3. The set is now 103 tasks.
- T098 `reference-check` trap (an over-broad instructor delete policy) passed every test: the other instructor cannot see the spots, so the delete matches nothing. Not a real hole; dropped the trap. Tests unchanged.

## 2026-10-25 — split frozen

- Committed all work so far on branch `rls-bench-v0`.
- Froze `tasks/split.json` with `rls split --freeze` (seed 20261025, stratified by tier): 72 train / 11 dev / 20 test (tier 1: 22/3/6, tier 2: 32/5/9, tier 3: 18/3/5). `freeze` refuses to run if the file exists; a pytest checks the split stays disjoint and within the task set.
- Note: 4 of the 20 test tasks (T001, T002, T009, T012) were already baselined against frontier and open models in Phase 2; their prompts were sent to OpenRouter, which is acceptable for evaluation but they must never be used to build SFT data.

## 2026-10-25 — open-model baselines on all 103 tasks

- Ran T014–T103 for Nemotron-3.5-Lightning (reasoning off, $0.08; 16k, $0.75), Qwen3-14B (16k, $0.55) and DeepSeek V4.1 Flash (16k, $3.38). No spend cap hit. Qwen3.8-27B skipped: its worst case ($21.66) exceeded the $20 per-run limit and 86% of its earlier answers were cut off.
- `summary.json` now has `by_split` (train/dev/test, from the frozen split) with the same rates plus pass@5.
- Nemotron reasoning-off (the training base), all 103 tasks: pass@1 12%, leak 25%, apply errors 50% (most common: syntax errors 131/618 samples, references to missing tables or columns 112/618). Train split pass@5 is 18%, so plain GRPO would see few rewarded groups; SFT first, as planned.
- DeepSeek V4.1 Flash is the strongest open model (pass@1 55%, train pass@5 85%, leak 1%) and is the natural source for rejection-sampled SFT data (spec §8.1). 37% of its answers were cut off at 16k tokens.

## 2026-10-25 — SFT data builder and dry run

- Added `train/build_sft.py`: rejection sampling from DeepSeek V4.1 Flash on the frozen train split only (dev/test refused by assertion), 16 samples per task at temperature 0.8, keep passing answers, dedupe by normalised SQL (comments, case and whitespace ignored), keep at most 6 per task, plus the reference solution. Raw samples go to `data/sft_raw.jsonl`, training rows to `data/sft.jsonl` in the exact §7.1 chat format. Offline tests cover the split guard, dedupe and the output shape.
- Dry run on 5 train tasks (T003–T007): 80 samples, $0.30. 69/80 passed, 0 leaked; every task reached the 6-answer cap; T007 lost 7/16 samples to the 16k-token cut-off. Examples are ~1,000 tokens (max ~2,400), within the planned 4,096 training length. 35 examples written.
- Full-run estimate: the script's formula says $2.17 typical / $11.16 worst for all 1,152 samples, but the dry run's actual cost ($0.00375/sample) implies ≈ $4.02 for the remaining 1,072. Expected yield is at most 72 × 7 = 504 examples, below the spec's 600–1,200 (written for 140 train tasks).

## 2026-10-25 — full SFT sampling stopped by the OpenRouter key limit

- Failure: the full run crashed after 873 of 1,152 samples (55 of 72 train tasks) with HTTP 403 from OpenRouter. The key info endpoint shows the key has a $20 spending limit, now used up ($20.03 used, $0 remaining), separate from the project's $60 budget. The crash also skipped the rebuild, leaving the dry-run `sft.jsonl`.
- Fix: `openrouter.complete` now keeps OpenRouter's error text in the exception (no key in it), and `build_sft.sample` stops cleanly on an API error so the training file is still rebuilt. Rebuilt `data/sft.jsonl` from the 873 saved samples (no cost).
- Yield so far: 334 examples (279 model answers + 55 references) over 55 tasks; 42 tasks at the 6-answer cap; T052 and T078 have no passing answer (reference only). Pass rate 64% (tier 1 85%, tier 2 58%, tier 3 42%); 199 samples cut off at 16k tokens. 17 train tasks not yet sampled (T079–T103 range); ≈ $1.60 more at the observed $0.0057/sample.

## 2026-10-25 — SFT sampling completed

- After the key limit was raised to $30, resumed sampling: 279 remaining samples, $1.46, no errors. All 1,152 samples (72 train tasks × 16) are recorded; total sampling cost $6.45.
- Final `data/sft.jsonl`: 427 examples (355 DeepSeek answers + 72 references) over all 72 train tasks; no dev/test task present (asserted). By tier: 1 → 145 examples (pass rate 83%), 2 → 191 (54%), 3 → 91 (39%). 50 tasks reached the 6-answer cap; T052 and T102 (both tier 3) have only the reference. 295 samples (26%) were cut off at 16k tokens, mostly tier 2–3. Examples are ~1,170 tokens (max ~2,800), ~0.52M tokens in total.

## 2026-10-25 — Tinker SFT script and dry run

- Added pinned deps `tinker==0.35.0` and `tinker-cookbook==0.5.8`. Tinker lists both training candidates (`nvidia/NVIDIA-Nemotron-3.5-Lightning-30B-A3B-BF16`, `Qwen/Qwen3-8B`); prices from the official page as of 2026-10-19: Nemotron-3.5-Lightning $0.184 prefill / $0.495 sample / $0.44 train per 1M tokens (64K context, shown 50% off), Qwen3-8B $0.195 / $0.60 / $0.44.
- Added `train/sft_tinker.py`, following the cookbook's `sl_loop` recipe: LoRA rank 32, 3 epochs, batch 16, max length 4,096, linear LR decay, Adam (0.9, 0.95), loss on the assistant answer only, final checkpoint (state + sampler) recorded in `results/train/checkpoints.json`, per-step metrics in `results/train/`. Refuses dev/test examples; stops before exceeding a spend cap.
- Deviations from spec §8.2: (1) the renderer is `nemotron3_ultra_disable_thinking`, the cookbook's recommended reasoning-off renderer for Nemotron-3.5-Lightning; (2) there is no "cookbook default LR" for this model — `hyperparam_utils.get_lr` raises NotImplementedError for all Nemotron models — so the default is 1e-4, the cookbook's minimal-SFT recipe value, exposed as `--learning-rate`.
- Dry run (local tokenization, no Tinker calls): 427 examples, 511,810 tokens per epoch, 277,265 trained tokens, 0 truncated (max 2,586), 78 steps; estimated training cost $0.66. Decoded one example: system + user + assistant turn with an empty `<think></think>`, loss only on the SQL answer and end token.

## 2026-10-25 — SFT run 1 failed before training (no spend)

- Failure: `sft_tinker.py --yes` raised `TinkerError: ... set the TINKER_API_KEY environment variable` when creating the ServiceClient. The key is in `.env`, but unlike `eval/openrouter.py` the script never loaded it. No training call was made, so nothing was billed; an empty `results/train/runs/` directory was left behind.
- Fix: load `TINKER_API_KEY` from `.env` into the process environment (without printing it) before creating the Tinker client; verified with a free capabilities call before rerunning.

## 2026-10-25 — SFT run 2 completed

- `sft_tinker.py --yes --max-spend 5` with defaults (Nemotron-3.5-Lightning, LoRA rank 32, LR 1e-4 linear decay, 3 epochs, batch 16, seed 0, data hash 3804db6d4692dcc5): run `20261025T125454Z`, all 78 steps, not stopped at cap, estimated spend $0.66.
- Train mean NLL per target token: step 0 0.364 → step 77 0.134; epoch means 0.251 / 0.157 / 0.127. Steepest drop in epoch 1, slow decline after; train loss only (no held-out loss was computed), so it says nothing yet about dev pass rate or overfitting.
- Checkpoint (state + sampler) recorded in `results/train/checkpoints.json`; per-step metrics in `results/train/sft_NVIDIA-Nemotron-3.5-Lightning-30B-A3B-BF16_20261025T125454Z.jsonl`, plotted with `train/plot_loss.py` to the `.svg` beside it.

## 2026-10-25 — Dev eval of SFT run 20261025T125454Z on Tinker

- Added `train/eval_tinker.py`: samples a Tinker checkpoint or base model with the baseline protocol (fixed prompt, 1 greedy + 5 at temperature 0.7, max 4,096 tokens, reasoning-off renderer), grades with the harness, writes baseline-format records to `results/tinker_eval/<label>.jsonl` plus `<label>.summary.json`. Refuses the test split.
- Ran the SFT checkpoint and the untrained base model on the 11 dev tasks, $1 cap each: 66 samples each, estimated spend $0.030 each, no errors.
- Dev results (from the records; 95% Wilson intervals):
  - Tinker base: greedy pass@1 1/11 (9%), pass@5 9%; all samples 6/66 (9%, [4%, 18%]); leak 39%, apply error 44%.
  - Tinker SFT: greedy pass@1 2/11 (18%), pass@5 27%; all samples 10/66 (15%, [8%, 26%]); leak 35%, apply error 32%.
  - OpenRouter reasoning-off (earlier run): all samples 10/66 (15%); leak 26%, apply error 55%. OpenRouter 16k reasoning: 13/66 (20%); 11 samples truncated.
- Reading: SFT moved the base in the right direction (fewer apply errors; T074 0/6 → 3/6, T081 0/6 → 1/6), but the intervals overlap and leak rate barely changed (39% → 35%). SFT on passing answers does not teach the model to avoid leaks; the harness reward in GRPO targets exactly that. Tinker base scores below OpenRouter reasoning-off (9% vs 15%), so the like-for-like comparison is Tinker base vs Tinker SFT.

## 2026-10-25 — GRPO script and dry run (no spend)

- Refactored `train/eval_tinker.py` so its sample-and-grade loop is reusable (`sample_and_grade`); behaviour unchanged.
- Added `train/rl_tinker.py`, following the cookbook's `rl_loop` recipe (group-centred rewards, constant-reward groups dropped, `importance_sampling` loss, no KL penalty = cookbook default). Starts from SFT run 20261025T125454Z's state. Commands: `filter` (sample the SFT model 8× per train task, keep tasks whose rewards are not all equal) and `train` (GRPO, dev eval with the baseline protocol every 5 steps on a saved checkpoint, early stop after 10 steps without dev improvement, spend cap). Rollouts, per-step metrics and checkpoint records go under `results/train/`.
- Reward: 1 pass, 0 safe failure (block / apply error), −0.1 format error (spec §6.4), and −0.5 for a leak (an addition to §6.4).
- Deviations from v1 §8.3: max completion 2,048 tokens instead of 1,024 (18% of the SFT model's dev answers exceed 1,024; median 600, p90 1,067); LR 4e-5 (rl_loop default; no calibrated Nemotron LR); dev selection uses pass rate over all 66 dev samples rather than 11 greedy samples (less noisy); tasks that always fail but sometimes leak are kept, because the leak penalty gives them signal.
- Dry run: all 72 references score 1.0; of 200 traps, 180 score −0.5 (leak) and 20 score 0.0, none 1.0. Estimates: filter $0.26 typical / $0.64 worst; smoke run (2 steps, group 2) ≤ $0.02; full run (50 steps × 8 tasks × 8 rollouts, 10 dev evals) $3.78 typical / $8.66 worst, before any task is dropped by the filter.

## 2026-10-25 — GRPO filter pass and smoke run

- Filter (`rl_tinker filter --max-spend 1`): SFT checkpoint sampled 8× at temperature 1.0 (max 2,048 tokens) on all 72 train tasks; 576 rollouts, estimated spend $0.25. Pass 19%, leak 15%, 62 format errors (mostly allowlist violations, 9 without a ```sql block), 3 truncated, mean 672 tokens. By tier: 1 → pass 49%, leak 15%; 2 → 8%, 18%; 3 → 3%, 8%. Kept 70 tasks; dropped T094 (8/8 pass) and T008 (8/8 safe failures, reward 0). 40 tasks never passed; 39 of them stay in only because leak/format rewards vary, so most groups teach "fail closed" rather than "pass". Raw rollouts: `results/train/rl_filter_20261025T125454Z.jsonl`.
- Smoke run (`train --steps 2 --group-size 2 --tasks-per-step 2 --eval-every 0 --max-spend 0.1`): run 20261025T133312Z, both steps completed, 1 of 2 groups trained per step, estimated spend $0.005, no errors; final checkpoint recorded in `results/train/checkpoints.json` (kind `rl`, 2 steps; a smoke test, not a model to evaluate).

## 2026-10-25 — GRPO run 20261025T133618Z (early-stopped at step 25)

- `rl_tinker train --max-spend 10` with defaults (70 filtered tasks, 8 tasks × 8 rollouts per step, temperature 1.0, max 2,048 tokens, LR 4e-5, leak penalty 0.5, dev eval every 5 steps). Stopped at step 25 by the patience rule (no dev improvement since step 15); estimated spend $1.51 including 5 dev evals. No errors. Console log copied to `results/train/runs/rl_…_20261025T133618Z/stdout.log`.
- Train mean reward per step was noisy (−0.16 to +0.56, 8 different tasks each step); 5-step mean rose from about +0.10 to +0.15–0.22. Groups with signal: 7–8 of 8 on most steps.
- Dev, all 66 samples (95% Wilson): SFT 15% pass [8, 26], leak 35% [24, 47] → step 5 17% / 29% → step 10 15% / 24% → **step 15 30% [21, 42] / 21% [13, 33]** → step 20 24% / 18% → step 25 15% / 18% [11, 29]. Greedy pass@1: 2/11 at SFT, 3/11 at step 15. Format errors fell to 0 from step 10; mean answer length 695 → ~440–480 tokens.
- Reading: the leak rate fell steadily (35% → 18%), which is what the leak penalty targets. The pass-rate peak at step 15 comes from three tasks (T028 0→3/6, T074 3→5/6, T081 1→6/6) that swing between evals, so it is noisy; and because the best of five evals was picked on dev, 30% is optimistic. Shorter answers are a reward-hacking signal to watch; format errors went to 0 without reward rising, so not conclusive. The test split is still untouched.
- Best dev checkpoint: step 15, sampler `results/train/checkpoints.json` → run 20261025T133618Z → `dev_evals[step 15].sampler_path`.

## 2026-10-25 — One-time test eval script (not run)

- Added `train/test_eval.py`: base, SFT 20261025T125454Z and the RL run 20261025T133618Z's best dev checkpoint (step 15) on the 20 test tasks, same protocol as dev (1 greedy + 5 at temperature 0.7, max 4,096 tokens). Guards: `--estimate` makes no calls and writes nothing; a real run needs `--yes --once` and a clean git tree, and writes `results/test_eval/LOCK.json` (models, paths, protocol, commit) before the first sample; with a lock, only the identical evaluation may rerun (to finish a crash). `eval_tinker` gained an `out_dir` parameter so test records live in `results/test_eval/`; the dev eval still refuses the test split.
- Estimate: 120 samples per model, 68,550 prompt tokens; $0.10 typical / $0.26 worst per model, $0.31 / $0.77 for all three.
- Note: the OpenRouter baselines (Phase 2–4) already ran on all 103 tasks, test included, before the split was frozen; no training choice (data, hyperparameters, checkpoint) used test results.

## 2026-10-25 — One-time test eval (20 test tasks)

- `train/test_eval.py --yes --once --max-spend 1` at commit 1bc6904; lock written 2026-10-25T14:33:25Z. 120 samples per model, no errors; estimated spend $0.063 (base) + $0.053 (SFT) + $0.043 (SFT+RL step 15) = $0.16.
- All samples (95% Wilson; samples are clustered by task, so these intervals are too narrow):
  - base: pass 13% [8, 21] (16/120), leak 29% [22, 38], apply error 42%, mean 848 tokens.
  - SFT: pass 23% [17, 32] (28/120), leak 19% [13, 27], apply error 35%, 678 tokens.
  - SFT+RL: pass 24% [17, 33] (29/120), leak 18% [12, 25], apply error 26%, 513 tokens.
  - Greedy pass@1 (n = 20): 15% / 30% / 25%; greedy leak: 25% / 25% / 35%.
- Task-level paired sign tests (pass count out of 6; leak count out of 6): SFT vs base, pass better on 4 tasks / worse on 2 (p = 0.69), leak lower on 10 / higher on 6 (p = 0.45). SFT+RL vs SFT: 3 / 2 (p = 1.00), leak 7 / 3 (p = 0.34). SFT+RL vs base: 6 / 1 (p = 0.12), leak 10 / 3 (p = 0.09).
- By tier, pass / leak: base 42% / 42%, 2% / 31%, 0% / 10%; SFT 53% / 14%, 17% / 17%, 0% / 30%; SFT+RL 72% / 22%, 4% / 9%, 3% / 27% (tiers 1 / 2 / 3).
- Reading: SFT is where most of the gain came from (pass 13% → 23%, leak 29% → 19%). GRPO did not add pass rate on test (23% → 24%); the dev jump at step 15 (15% → 30%) did not hold, as expected from picking the best of five dev evals on 11 tasks. GRPO did cut apply errors (35% → 26%) and shortened answers (678 → 513 tokens), and its pass gains sit in tier 1 (53% → 72%) while tier 2 fell (17% → 4%) — the "tier 1 improving while traps don't" pattern from spec §8.3. No difference is significant at task level with 20 tasks; base → SFT+RL is the strongest (pass p = 0.12, leak p = 0.09).

## 2026-10-25 — Training section of the write-up drafted

- Created `docs/writeup.md` with the §11 outline; only §5 (training) is drafted. Every number in it is produced by repo code and stored under `results/`: added `train/build_sft.py stats` → `results/train/sft_data_stats.json`, `train/spend.py` → `results/train/tinker_spend.json` (total Tinker spend $2.65, estimated at list prices; the filter pass cost is recomputed from token counts), and `train/report.py` → `results/train/report.json` (dev/test tables with Wilson intervals, test by tier, paired sign tests). These replace earlier one-off snippets.

## 2026-10-26 — Version 2 training plan started

- Plan in `docs/spec.md` §8.2. Dependencies added and pinned: `anthropic==2.3.0` (Claude through the Anthropic API instead of OpenRouter) and `matplotlib==3.11.2` (figures).
- New code: `train/rl_env.py` (harness as a cookbook RL environment, single- or multi-turn with feedback, spend guard, dev evaluator), `train/rl_cookbook.py` (GRPO on the cookbook loop), `train/sft_cookbook.py` (SFT on the cookbook loop with a dev-loss evaluator and learning-rate sweep), `train/prices.py`, `train/leaderboard.py`, `eval/anthropic_client.py`, `build_sft.py dev-set` (57 dev examples: 11 references + 46 passing DeepSeek baseline samples on dev tasks).
- Dry runs (no spend): all 72 references score 1 through the environment; traps score −0.5 (180) or 0 (20). SFT sweep on Qwen3.5-9B: 78 steps per run, 1.57M train tokens, $2.47 per learning rate. GRPO on Qwen3.5-9B at 60 steps × 24 tasks × 8 rollouts has a worst case of $67, over the $40 cap, so the run is sized at 50 × 16 × 8 (6,400 rollouts; typical $17, worst $36). Opus 5.5 on 103 tasks: typical $38 at 8,000 max tokens, run with a $45 cap on the Anthropic credit. Tinker leaderboard: Qwen3.5-9B, gpt-oss-120b, DeepSeek V4.1 Flash, Kimi K2.6, reasoning off, 4,096 tokens, $7 cap per model (Qwen3.8-27B dropped: $5.4 typical for a model already on the 13-task table).
- Concurrency check: 12 harness grades in parallel (4 at a time) all passed in 1.2 s; the RL environment grades 4 rollouts at a time.

## 2026-10-26 — SFT sweep, Qwen3.5-9B (cookbook loop)

- Three runs, 78 steps each (427 examples, batch 16, 3 epochs, rank 32, linear decay), dev loss on 57 held-out dev-task examples every 10 steps. Final dev NLL: lr 1.58e-4 → 0.1446, **lr 4.73e-4 (calibrated) → 0.1413**, lr 1.42e-3 → 0.1474. Training loss ended at 0.083 / 0.061 / 0.063. Estimated $2.47 per run. The SFT model is run 20261025T184758Z; `results/train/sft_sweep_Qwen3.5-9B_*.json`.
- GRPO learning-rate sweep started from it: 2e-5, 6e-5, 2e-4; 10 steps × 16 tasks × 8 rollouts each, dev eval at step 10 (typical $3.3, worst $7.3 per run).

## 2026-10-26 — Leaderboard run stopped at DeepSeek (Tinker)

- Failure: `train/leaderboard.py run` finished Qwen3.5-9B and gpt-oss-120b (618 samples each), then Tinker returned `400 Sampling is not supported for deepseek-ai/DeepSeek-V4.1-Flash-1017` (the model is listed for training only); Kimi K2.6 never started. No money lost beyond the two finished rows.
- Fix: DeepSeek removed from the Tinker leaderboard models (its OpenRouter row on all 103 tasks stands); Kimi rerun alone. Consequence for experiment C: a Tinker-sampled teacher must be Kimi K2.6 or another sampleable model.
- Experiment C note: the cookbook's on-policy distillation scores the student's own token sequence with a teacher sampling client (`compute_logprobs`, prefill rate), so the teacher must share the student's tokenizer. For Qwen3.5-9B the candidate teacher is Qwen3.5-397B-A17B ($1.65 prefill); it would need its own 103-task baseline first (~$4) to show it is worth distilling from. Decided at the end from the remaining budget.

## 2026-10-26 — Zero-shot judges (first results)

- Judge data (`train/judge.py build`): 2,352 train / 160 dev / 400 test examples, balanced over pass / leak / block / error, deduplicated by (task, normalised SQL); `results/judge/data_stats.json`.
- Failure: gpt-oss-120b (medium-reasoning template, the only chat template it has) produced no verdict within 32 output tokens (392 of 400 unparsed) and still 119 unparsed at 600. Fix: verdicts are parsed as the last label word in the answer, and reasoning judges get 1,500 output tokens; 5 unparsed remain.
- Kimi K2.6 with thinking off (one-word answers): accuracy 37%, κ 0.16, leak recall 34%, leak precision 24%. gpt-oss-120b with reasoning (1,500 tokens): accuracy 52%, κ 0.36, leak recall 82%, precision 42%. Kimi with thinking on added as a row to separate "reasoning on/off" from "which model".

## 2026-10-26 — Dev reference points for the Qwen3.5-9B student

- Dev (11 tasks × 6 samples), reasoning off: base 0% pass, 12% leak, 59% apply errors, 1,475 tokens per answer (from the leaderboard file, dev tasks only); SFT run 20261025T184758Z 24% pass, 26% leak, 24% apply errors, 531 tokens. GRPO sweep run at lr 2e-5 after 10 steps: 21% pass, 42% leak, 12% apply errors (train-side: pass 43% → 47%, leak 13% → 6%, KL ≈ 1e-4, entropy 0.082 → 0.054). The leak rise on dev after 10 steps is within noise for 11 tasks; judged again with the other two learning rates.

## 2026-10-26 — Trained judge (experiment D, first results)

- Judge: Qwen3-8B LoRA (rank 32, lr 4.73e-4 calibrated, 2 epochs, 294 steps, batch 16) on 2,352 balanced train-task examples; dev NLL 3.92 → 0.45 (min 0.44); estimated $3.3. Run 20261025T185503Z.
- On the 400 held-out test-task candidates (100 per label): trained judge accuracy 61% [56, 66], κ 0.48, leak recall 53%, leak precision 62%, 10% of real leaks called "pass". Zero-shot gpt-oss-120b with reasoning: accuracy 52%, κ 0.36, leak recall 82%, leak precision 42%, 0% of leaks called pass but 36 of 100 passing answers called leaks. Kimi K2.6: κ 0.16 with thinking off (leak recall 34%) and with thinking on (leak recall 59%, 19 unparsed). Opus pending. Files: `results/judge/`.

## 2026-10-26 — SFT sweep, Nemotron-3.5-Lightning (cookbook loop)

- Same recipe as the Qwen sweep; no calibrated rate exists for Nemotron, so lr 3e-5 / 1e-4 / 3e-4. Final dev NLL 0.205 / 0.159 / **0.153** (min 0.148 at 3e-4); training loss 0.18 / 0.11 / 0.066. The best point sits at the top of the sweep, so a higher rate might do slightly better; not pursued (about $0.7 per run, small expected gain). SFT model: run 20261025T190749Z. GRPO mini-sweep (2e-5, 6e-5; 10 steps × 16 × 8) started from it, plus its dev reference eval.
- Nemotron dev reference (11 tasks × 6 samples): base 9% pass / 39% leak; v1 SFT (hand loop, lr 1e-4) 15% / 35%; v2 SFT (cookbook loop, lr 3e-4) 30% / 44%, apply errors 44% → 12%, 584 tokens per answer. Tuning the learning rate alone doubled the dev pass rate; the leak rate did not improve, which is GRPO's job.

## 2026-10-26 — GRPO learning-rate sweep, Qwen3.5-9B (10 steps × 16 tasks × 8 rollouts, from the SFT model)

- lr 2e-5: train reward 0.27 → 0.35, pass 37% → 43%, leak 20% → 14%, entropy 0.082 → 0.054, dev after 10 steps 21% pass / 42% leak. lr 6e-5: reward 0.32 → 0.47, pass 41% → 54%, leak 18% → 15%, entropy 0.079 → 0.022, dev 21% / 39%. lr 2e-4: reward 0.30 → 0.12, pass 41% → 20% (collapsed), dev 20% / 39%. Sampler-trainer KL ≤ 5e-4 throughout. About $3.1 per run.
- Decision: the full run uses lr 4e-5 (between the stable 2e-5 and the fast-but-entropy-collapsing 6e-5; also the cookbook's RL default), 50 steps × 16 × 8, dev eval every 10 steps, cap $40 (worst case $37.6).
- Watch item: all three runs raised the dev leak rate above the SFT model's 26% while cutting dev apply errors (24% → 12–20%): SQL that used to fail to apply now applies and leaks. Train-side leak rates fell. Reported either way; the pre-registered selection rule (highest dev pass) stands.
- Per-sample dev transitions SFT → GRPO (lr 2e-5, 10 steps): 8 apply-error samples became leaks (all on T073 and T067), 2 passes became leaks (T028), 1 blocked sample became a leak; nothing moved into pass. The early policy change on unseen tasks is "write SQL that applies", in the style of passing train answers, and on T073/T067 that style leaks. The 50-step run's dev evals will show whether leaks come back down.

## 2026-10-26 — Repair-RL dry run (experiment B, not started)

- Environment check with 3 turns: all 72 references score 1 on the first try; every trap gets feedback and a second turn (no episode ends early). Estimate at 30 steps × 16 tasks × 4 rollouts with 2,048-token answers: typical $13, worst $56 (three turns, each re-reading the growing conversation), over the $40 cap. The run will use 25 steps and 1,536-token answers (worst ≈ $35), starting from the best single-turn GRPO checkpoint once that run finishes.
