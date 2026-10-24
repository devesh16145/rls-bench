A polling app built with supabase-js. Users vote, or change their vote, with `supabase.from('votes').upsert({ poll_id, user_id, option_id }).select()`, and withdraw with `.delete()`. Results are computed on the server. A poll is open while `closes_at` is in the future (compared with `now()`).

R1. Signed-in users can read every poll and every option.
R2. Users can see only their own votes.
R3. Users can vote once per poll, as themselves, only for an option that belongs to that poll, and only while the poll is open.
R4. While a poll is open, users can change their vote (again only to an option of that poll) or withdraw it. Votes on closed polls can no longer change.
R5. Nobody can change polls or options through the app.
R6. Anonymous visitors cannot see or change anything.
R7. Server-side code using the service role keeps full access.

RLSBENCH-CANARY-f9002c750838f00b
