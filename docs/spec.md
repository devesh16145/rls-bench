# RLS-Bench specification (v2, 2026-10-24)

Revision of the original brief. Changes from v1: a 14-day resume-first plan (§10), statement-level output allowlist (§5.1), rule IDs instead of sentence splitting (§5.2), a `denied` expectation (§5.2), trap mutations (§6.3 check 8), `auth.users` in the shim and a `nullif` fix in `auth.uid()` (§6.1), `create trigger` allowed in the output contract, and confidence intervals in all reported metrics (§7.3).

## 1. What this is and why

A public, verifiable benchmark for Supabase/Postgres Row Level Security (RLS), baselines of frontier and open models, and a study of how well an LLM judge agrees with executable truth. Then a small open model fine-tuned with SFT and RL (GRPO) on Tinker, using the harness as the reward.

It shows, with public evidence, that the owner can do AI-training and AI-evaluation work: write coding tasks with verifiable answers, evaluate AI-generated code rigorously, and build training data. It is not a product.

Owner: solo developer in India, daily Supabase/React/Android experience, ~10–12 h/week. Budgets: ~$350 Claude Code credits, up to $60 OpenRouter, $150 Tinker.

Why RLS: the 2025 vibe-coding breaches (Lovable-built apps exposing data through missing policies, the Base44 auth bypass) were authorization failures. Models write RLS badly in specific, repeatable ways.

## 2. Rules

See `CLAUDE.md`. They apply to every phase.

## 3. Decisions already made

| Decision | Choice |
|---|---|
| Ground truth | Executable tests in Postgres |
| Harness | Postgres 16 + a small Supabase-compatible `auth`/`storage` shim. Backends: Docker `postgres:16` if a daemon is reachable, else the `pgserver` package (embedded binaries), else `pg_ctl` on PATH. |
| Size | v0.1: 30 tasks (baselines, judge). Training needs more: at least 100, target 200 (70/10/20 split of the final count, stratified by tier; 140/20/40 at 200). |
| Baselines | 3–4 frontier models for v0.1, 6–8 for v1.0, through OpenRouter. pass@1 at temperature 0 (or the provider default where temperature is ignored, recorded), pass@5 at 0.7. |
| Output contract | One ```sql block, statement allowlist in §5.1 |
| Public artifacts | GitHub repo (MIT code, CC-BY-4.0 tasks), write-up, later a static leaderboard and HF dataset |

## 4. Repository layout

```
CLAUDE.md, README.md, LICENSE, pyproject.toml, .env.example
.github/workflows/validate.yml
harness/  db.py shim.sql models.py sqlparse.py runner.py checks.py mutations.py card.py cli.py
tasks/T###-slug/  task.yaml schema.sql seed.sql requirement.md tests.yaml solution.sql traps/<trap-id>.sql
eval/     prompts.py openrouter.py run_baselines.py judge.py metrics.py      (Phase 2+)
train/    build_sft.py sft_tinker.py rl_tinker.py eval_checkpoint.py          (optional phase)
results/  baselines/*.jsonl  summary.json
docs/     spec.md authoring-guidelines.md failure-taxonomy.md log.md ideas.md writeup.md
tests/    pytest for the harness
```

## 5. The benchmark

### 5.1 Task and output contract

A task gives the model a schema (no policies) and numbered access rules written like a product spec. The model returns SQL that makes the rules hold.

Allowed statements (checked per statement, after splitting on `;` outside quotes, dollar-quotes and comments):

- `alter table <t> enable|force row level security`
- `create [or replace] function` (not in schemas `auth`, `storage`, `pg_catalog`, `information_schema`)
- `create [constraint] trigger`
- `create policy`, `drop policy [if exists]`, `alter policy`
- `create [or replace] view`, `alter view ... set (...)`
- `create schema`
- `grant`, `revoke`
- `create index`
- `comment on`

Anything else (inserts, updates, deletes, table DDL, role changes, `set`, `do` blocks…) or no ```sql block is a `format_error`: a failure, counted separately, never applied.

### 5.2 Task files

`task.yaml`
```yaml
id: T002
title: Team documents with viewer and editor roles
tier: 2                 # 1 basic, 2 relational, 3 hard
tags: [team-membership, role-column, soft-delete]
traps: [weak-with-check, forgot-enable]
extra_tables: []        # non-public tables the task covers, e.g. [storage.objects]
verified: false         # only the owner flips this
author: owner
created: 2026-10-24
canary: "RLSBENCH-CANARY-<16 hex, identical across tasks>"
```

`schema.sql` — tables, indexes, FKs. No policies, RLS not enabled.
`seed.sql` — fixture rows using fixed UUIDs (users go in `auth.users`).
`requirement.md` — a one-paragraph context, then rules `R1.`…`Rn.` one per line, then the canary on its own line.
`solution.sql` — owner's reference solution. Never shown to models; no comments hinting at traps.
`traps/<trap-id>.sql` — the reference solution with exactly that trap planted. Must fail.

`tests.yaml`
```yaml
- name: viewer_cannot_insert
  covers: [R4]
  as: {role: authenticated, sub: "00000000-0000-0000-0000-000000000003"}
  sql: insert into documents (team_id, title, created_by) values (1, 'x', '00000000-0000-0000-0000-000000000003')
  expect: {error: "42501"}
```
Expectation kinds (exactly one per test):
- `rows`: exact ordered rows. Values compared after normalisation (uuid/decimal/date → text). More than one row requires `order by`.
- `count`: number of rows returned.
- `affected`: rowcount of a write. RLS silently filters updates/deletes, so `0` vs `1` matters.
- `error`: SQLSTATE string.
- `denied`: the write did nothing, by any mechanism: SQLSTATE `42501`, `P0001` or `23514`, or rowcount 0. Unique and foreign-key violations do not count. Use this instead of `error` whenever several correct implementations would block differently (trigger vs policy).

Tests may hold several statements; the last statement's result is compared. `denied` also applies to reads (permission error or zero rows passes; any row is a leak).

`as` takes `role` (`anon` | `authenticated` | `service_role`), optional `sub`, optional `claims:` merged into the JWT claims JSON.

### 5.3 Tiers

- **Tier 1:** single-table ownership, public read + owner write, insert checks, per-user settings, anon vs authenticated.
- **Tier 2:** membership via join tables, role column, admin via claim or profiles table, soft delete, publish windows, column restriction via `security_invoker` views, parent/child visibility.
- **Tier 3:** org → project → item hierarchies, `security definer` helpers to avoid recursion, `storage.objects` path policies, RPCs that must check auth, expiring share links, restrictive + permissive combinations, delegated access.

### 5.4 Traps

See `docs/failure-taxonomy.md` for the canonical list. Every Tier 2–3 task plants at least one trap, lists it in `traps:`, and ships `traps/<trap-id>.sql` proving a test catches it.

### 5.5 Authoring guidelines

See `docs/authoring-guidelines.md`.

## 6. Harness

### 6.1 Shim

`harness/shim.sql`, applied once to the template database `rlsbench_template`. Roles `anon`, `authenticated`, `service_role` (bypassrls); `auth.users`; `auth.uid()`, `auth.jwt()`, `auth.role()`; `storage.buckets`, `storage.objects` (RLS enabled, as in Supabase), `storage.foldername()`, `storage.filename()`; Supabase-style default privileges so RLS is the only gate.

The harness connects as a superuser (like the `postgres` role in Supabase's SQL editor). `set local role` switches to the simulated role, so RLS applies to `anon`/`authenticated` and is bypassed by `service_role`.

### 6.2 Running a candidate

1. `create database run_<hex> template rlsbench_template`.
2. Apply `schema.sql`, `seed.sql`.
3. Format check (§5.1); if it fails, stop with `format_error`.
4. Apply candidate with `statement_timeout = 10s` in one transaction. Error → `apply_error` (SQLSTATE + message).
5. Each test: `begin; set local role <r>; set_config('request.jwt.claims', <json>, true); set local statement_timeout = '5s'; <sql>; rollback`.
6. Compare (`harness/checks.py`). Classify each failing test as `leak` (more access than expected) or `block` (less).
7. Drop the run database.

`TaskResult`: `task_id, passed, tests[{name, passed, expected, observed, leak, block}], apply_error, format_error, leak, block, duration_ms`.

### 6.3 Validation (`rls validate`)

A task is valid only when all pass:

1. Reference passes every test.
2. Empty candidate fails ≥ 1 test.
3. Allow-all (`enable rls` + `for all to public using (true) with check (true)` on every task table) fails ≥ 1 test.
4. Deny-all (`enable rls`, no policies) fails ≥ 1 test.
5. Reference run twice gives identical observations.
6. Coverage: every rule ID in `requirement.md` is cited by ≥ 1 test; every `covers` ID exists.
7. Structure: ≥ 1 `anon` and ≥ 1 `service_role` test; Tier 2–3 list ≥ 1 trap; canary in `task.yaml` and `requirement.md`; multi-row `rows` tests use `order by`.
8. Trap mutations: every listed trap has `traps/<trap-id>.sql`, and each one fails ≥ 1 test.

### 6.4 RL reward (optional phase)

`1.0` if passed, else `0.0`; `-0.1` for format errors.

## 7. Baselines

### 7.1 Prompt (fixed for the project)

System: "You are a senior database engineer. Write Supabase Row Level Security for the schema and rules below. Available: `auth.uid()`, `auth.jwt()`, `auth.role()`, roles `anon`, `authenticated`, `service_role` (bypasses RLS). Output exactly one ```sql block containing only: `alter table ... enable row level security`, `create policy`, helper `create function`, `create trigger`, `create view`, and grants/revokes. Do not modify existing tables or data. No explanation outside the block."

User: `schema.sql` verbatim; a short description of the seed data shape (not the rows); `requirement.md` verbatim.

Zero-shot, no tools, no retries on format errors.

### 7.2 Protocol

Exact model IDs, run dates, reasoning-effort settings and max-token caps recorded in `results/summary.json`. Disk cache every response keyed by (model, task, temperature, index). Print running spend; cap $60 total. Reasoning models: cap max tokens and record whether temperature was honoured.

### 7.3 Metrics

pass@1, pass@5 (with n = 5 this is "any of 5 passed"), leak rate (headline), block rate, apply-error rate, format-error rate; by tier, tag, trap. Every rate is reported with a 95% Wilson interval.

### 7.4 Judge calibration

A frontier judge sees requirement + candidate SQL (never tests) and returns `pass|fail`, a taxonomy category, and one line of reasoning. Report Cohen's kappa against harness truth and judge precision/recall on `leak`.

## 8. Training on Tinker (required, Phase 4–5)

Same as v1: rejection-sampled SFT then GRPO on Tinker with the harness as reward, test split evaluated once. Before starting, confirm model availability and prices on Tinker's current list, filter out train tasks where every sample passes or every sample fails, and report confidence intervals (a 40-task test split has roughly ±15 pp).

## 9. Review process

Per task (≈5 min): read the requirement as a product manager (is every rule unambiguous?); for each rule, check one test that fails if the rule is ignored and one that fails if it is over-applied; read the solution (only what the rules say?); check the fixture has the edge rows the traps need; run `rls validate`; then set `verified: true`.

Claude prints the card with `uv run rls card <task>` and stops.

## 10. Phases and stop points (14-day plan)

**Phase 1 — days 1–3.** Harness, shim, CLI, pytest, CI, guidelines, taxonomy, three tasks (one per tier) validated, review cards. **Stop.**
Done when `rls validate --all` and `pytest` pass, a candidate run twice gives identical results, and the harness works without Docker.

**Phase 2 — days 4–7.** Seven more tasks → review → stop. Then `eval/openrouter.py`, `run_baselines.py`, `metrics.py`, `rls summarize`; baseline 2 frontier models on the 10 verified tasks; checkpoint (best frontier pass@1 on Tier 2–3 within ~30–85% → continue; > 90% on Tier 3 → harder tasks first; < 10% everywhere → check the harness). Then 20 more tasks to reach 30, baseline 3–4 models, README write-up with real numbers, push public. **Stop.** Resume bullets become real here.

**Phase 3 — days 8–14.** `eval/judge.py` over all temperature-0 samples, kappa and leak precision/recall, failure examples, `docs/writeup.md` (~1,500 words). **Stop** with a publish checklist.

**Phase 4 — scale for training (week 3).** Grow to at least 100 verified tasks (target 200) in batches of 10 with review stops; freeze `tasks/split.json`; baseline the open candidates for rejection sampling. **Stop.**

**Phase 5 — training on Tinker (week 4).** Confirm models and prices on Tinker first. `build_sft.py` (dry run on 5 tasks, then full), LoRA SFT, dev eval, GRPO (dry run 2 steps, group 2, then the real run), test evaluated once with the best dev checkpoint, adapter export. **Stop** with untrained / SFT / SFT+RL test numbers and curves in `results/train/`.

**Phase 6 — publish.** Leaderboard site, HF dataset and adapter, write-up with the training section.

## 11. Write-up outline

1. Why RLS. 2. Benchmark design, guidelines, traps, trap mutations. 3. Results with intervals, leak-rate chart, per-trap table, two quoted failures. 4. Judge calibration. 5. Limitations (synthetic schemas, Supabase flavour, small N, single author, contamination; canary published). 6. What's next.
