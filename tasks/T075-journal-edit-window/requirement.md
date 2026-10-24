A private journaling app built with supabase-js. Entries are written with `supabase.from('journal_entries').insert({ user_id, body, mood }).select()`; `created_at` defaults to the time of writing. Edits use `.update({ body, mood }).eq('id', id)`. Time is compared with `now()`.

R1. Users can read and write only their own journal entries.
R2. Users can edit and delete their own entries only within 24 hours of `created_at`; older entries are permanent.
R3. `created_at` is always the time of writing: users can never set or change it.
R4. Anonymous visitors cannot see or change anything.
R5. Server-side code using the service role keeps full access.

RLSBENCH-CANARY-f9002c750838f00b
