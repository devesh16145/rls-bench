An HR app built with supabase-js. Each employee has at most one manager (`manager_id`). Employees request leave with `supabase.from('leave_requests').insert({ employee_id, starts_on, ends_on, note }).select()`; the leave form saves with `.update({ starts_on, ends_on, note, status }).eq('id', id).select()`, sending every field on each save. Managers decide with `.update({ status, decided_by }).eq('id', id).select()`.

R1. Employees can read their own leave requests. Managers can read the requests of their direct reports, and only their direct reports.
R2. Employees can create leave requests for themselves only; new requests are pending with no `decided_by`.
R3. While a request is pending, its employee can change its dates and note or cancel it (status `cancelled`). Employees can never approve or reject their own requests.
R4. A direct manager can approve or reject a pending request of one of their reports, recording themselves in `decided_by`. Deciding cannot change the dates or the note.
R5. Once a request is no longer pending, nobody can change it. Requests are never deleted.
R6. Signed-in users can read the employee directory. Nobody can change `employees` through the app.
R7. Anonymous visitors cannot see or change anything.
R8. Server-side code using the service role keeps full access and is not bound by these rules.

RLSBENCH-CANARY-f9002c750838f00b
