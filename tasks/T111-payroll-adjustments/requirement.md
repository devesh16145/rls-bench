An HR tool built with supabase-js. `employees` holds each person's direct manager and whether they are in finance. Managers raise adjustments with `supabase.from('adjustments').insert({ employee_id, amount_cents, reason, created_by }).select()` and decide them with `supabase.from('adjustments').update({ status, approved_by }).eq('id', id).select()`. Amounts are in cents; the manager approval limit is 50,000.

R1. Employees can see their own adjustments. A manager can see the adjustments of their direct reports only (not of reports further down). Finance can see every adjustment. Users can see their own employee row, their direct reports' rows, and finance can see all rows.
R2. A direct manager can raise a pending adjustment for a direct report, as themselves; finance can raise one for anyone else. Nobody raises an adjustment for themselves.
R3. A pending adjustment of at most 50,000 can be approved or rejected by the employee's direct manager; above 50,000 only finance can decide it. The decision records the decider as `approved_by`, and nobody decides an adjustment for themselves.
R4. Once decided, an adjustment never changes. The employee, amount and reason never change through the app, and adjustments are never deleted through the app. Nobody changes `employees` through the app.
R5. Anonymous visitors cannot see or change anything. Server-side code using the service role keeps full access.

RLSBENCH-CANARY-f9002c750838f00b
