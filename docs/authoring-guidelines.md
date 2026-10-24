# Task authoring guidelines

## Requirements
- Describe behaviour, never implementation: "members can read", not "use a policy with exists".
- One rule per line, numbered `R1.` `R2.` …, after a one-paragraph context. End with the canary line.
- Every rule must be enforceable within the output contract (spec §5.1). If a rule needs to compare old and new rows, either allow a trigger-based answer (and test with `denied`) or rephrase it in terms of the new row.
- Always state the anon rule and the service-role rule explicitly.
- If two reasonable engineers could implement a sentence differently and get different test results, rewrite it.

## Tests
- Every rule has at least one test that fails if the rule is ignored and one that fails if it is over-applied.
- Every task has an `anon` test and a `service_role` test.
- Use `denied` for blocked writes unless the exact mechanism is part of the rule. Use `affected: 0` for updates/deletes that should silently match nothing, and `affected: 1` to prove an allowed write really happened.
- `denied` also works for reads that must show nothing: it passes on a permission error or zero rows, and counts any returned row as a leak.
- A test may contain several statements (e.g. call an RPC, then read the row it changed); only the last statement's result is compared.
- Prefer `client:` tests (supabase-js shaped: insert/update with `returning`, upserts) for writes, and say in the requirement's context how the app writes. Do not test client behaviour the requirement doesn't describe.
- Never hard-code ids that come from sequences unless the test creates them itself; the runner resets sequences before each test, so the first new id after the seed is stable.
- Multi-row `rows` expectations need `order by`.
- Remember Postgres checks an updated row against the SELECT policies too. A test for an update hole must use a row that stays visible to the user after the update.

## Fixtures
- Fixed UUIDs `00000000-0000-0000-0000-0000000000NN`; users go in `auth.users`.
- No `now()`: use `2020-01-01` or `2099-01-01`.
- Include the edge rows the traps need (NULL owner, soft-deleted row, row in another team, expired link, user in two groups, user in none) and list them in `fixture_notes`.
- `setval` identity sequences after inserting explicit ids.

## Traps
- Tier 2–3 tasks plant at least one trap from `docs/failure-taxonomy.md`.
- Each trap ships as `traps/<id>.sql`: the reference solution with only that mistake planted. `rls validate` proves a test catches it.

## Variety
- Realistic domains (invoices, tickets, courses, files), not `table_a`.
- No two tasks share a schema with only renamed columns.
