A garage app built with supabase-js. Mechanics open jobs with `supabase.from('jobs').insert({...}).select()` and update them with `.update({...}).eq('id', id).select()`. Customers approve a quote with `.update({ status: 'approved', quote_amount }).eq('id', id).select()`, sending back the amount they saw. Jobs move `quoted` → `approved` → `in_progress` → `done`.

R1. Signed-in users can see the list of garages. Customers can see their own jobs; mechanics can see every job of their garage.
R2. Mechanics can open jobs for their garage, always `quoted`, and can change a quote while the job is still `quoted`.
R3. Only the job's customer can approve a quoted job, and approving cannot change anything else about it, including the amount.
R4. Once a job is approved, mechanics of its garage can move it to `in_progress` and then `done`, without changing the quote. Mechanics can never approve on a customer's behalf.
R5. Jobs are never deleted, and nobody can change garages or mechanics through the app.
R6. Anonymous visitors cannot see or change anything.
R7. Server-side code using the service role keeps full access.

RLSBENCH-CANARY-f9002c750838f00b
