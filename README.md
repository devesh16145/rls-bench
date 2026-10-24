# RLS-Bench

A verifiable benchmark for Supabase/Postgres Row Level Security. Each task gives a schema and access rules written like a product spec; a model writes the policies; executable tests run queries as simulated users (`anon`, `authenticated`, `service_role`) and check exactly what each one can see and change.

Status: work in progress (harness + first tasks). No model results yet.

## Run it

```
uv sync
uv run rls db up            # Docker if available, else embedded Postgres (pgserver)
uv run rls validate --all   # mutation checks for every task
uv run rls run tasks/T001-personal-notes my_policies.sql
uv run pytest
```

## How tasks are validated

Every task must pass: reference solution passes; no-policy, allow-all and deny-all candidates fail; results are deterministic; every numbered rule is covered by a test; and every planted trap (`traps/<id>.sql`) is caught by at least one test.

## License

Code: MIT. Tasks under `tasks/`: CC-BY-4.0. The canary string `RLSBENCH-CANARY-f9002c750838f00b` marks benchmark data; please exclude it from training corpora.
