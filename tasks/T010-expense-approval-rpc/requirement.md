An expense tool. Users belong to departments; some members are managers (`is_manager`). Employees submit expenses, and managers approve or reject them. Implement the decision as the function `public.decide_expense(p_expense_id bigint, p_approve boolean) returns void`, which sets `status` to `approved` or `rejected` and records the caller's user id in `decided_by`.

R1. Users can read their own expenses, and managers can read every expense of the departments they manage.
R2. Users can submit expenses only as themselves, only to departments they belong to, with status `pending` and no decision recorded.
R3. Submitters can change the amount of their own pending expenses. Nobody can change `status` or `decided_by` by updating expenses directly.
R4. `decide_expense` succeeds only when the caller manages the expense's department, the expense is pending, and the caller did not submit it. In every other case it raises an error and changes nothing.
R5. Server-side code using the service role can call `decide_expense` on any pending expense; `decided_by` is then left empty.
R6. Users can see their own department memberships. Expenses cannot be deleted, and departments and memberships cannot be changed, through the app.
R7. Anonymous visitors cannot see anything or decide expenses.
R8. Server-side code using the service role keeps full access to all tables.

RLSBENCH-CANARY-f9002c750838f00b
