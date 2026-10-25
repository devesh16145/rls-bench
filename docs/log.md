# Run log

## 2026-10-24 — Phase 1

- `typer==0.12.5` fails with click 8.3 ("Secondary flag is not valid for non-boolean flag"). Fix: pin `click==8.1.7`.
- T001 trap `weak-with-check` (`with check (true)`) initially passed every test. Cause: Postgres checks the updated row against SELECT policies as well, so handing a *private* note to another user fails with 42501 regardless of `with check`. Fix: added test `ana_cannot_hand_public_note_to_ben`, which hands over a public note that stays visible after the update. The test was made stricter, not weaker. Recorded in the taxonomy and authoring guidelines.

## 2026-10-24 — Phase 2 (tasks T004–T010)

- Harness: tests may now contain several statements; the runner advances to the last result (`cur.nextset()`), needed for RPC tests in T010 that call a function and then read the row. No existing test changed result.
- T009: the owner-transfer test is caught by the read policy as well (after a transfer the old owner can no longer see the file), so only `editor_cannot_take_ownership` discriminates the `ownership-change` trap. Kept both; the card records which one catches it.
- The three Phase 1 tasks still read `verified: false` on disk at the start of Phase 2; flagged to the owner rather than changed.

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
- Change: `summary.json` now reports `truncation_rate` (greedy) and `truncation_rate_all_samples` per model. Results under the 16k protocol are kept as recorded; no rerun without owner approval.

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
- At the start of this batch T074–T083 still read `verified: false` on disk; flagged to the owner, not changed.

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
