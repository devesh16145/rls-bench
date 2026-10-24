An expense-splitting app built with supabase-js. Adding an expense inserts it with `supabase.from('expenses').insert({...}).select()` and then inserts one `expense_shares` row per person; edits use `.update({...}).eq(...).select()`.

R1. Members can see their groups and every member of those groups.
R2. Members can read every expense and every share in their groups.
R3. Members can add expenses to their groups, paid by themselves. Only the payer can edit or delete an expense, and an expense can never move to another group or get another payer.
R4. Only the payer of an expense can add, change or remove its shares, and every share must belong to a member of the expense's group.
R5. Groups and memberships cannot be changed through the app.
R6. Anonymous visitors cannot see or change anything.
R7. Server-side code using the service role keeps full access.

RLSBENCH-CANARY-f9002c750838f00b
