A product's public roadmap built with supabase-js. Users vote with `supabase.from('item_votes').insert({ user_id, item_id }).select()` and remove a vote with `.delete()`; the primary key allows one vote per user per item. The product team manages items from a server tool using the service role.

R1. Anyone, including anonymous visitors, can read the roadmap items.
R2. Signed-in users can see all votes. Anonymous visitors cannot.
R3. Signed-in users can vote, as themselves, on items that are not shipped, and can remove their own votes.
R4. Nobody can change roadmap items, or anyone else's votes, through the app.
R5. Server-side code using the service role keeps full access.

RLSBENCH-CANARY-f9002c750838f00b
