A campus lost-and-found built with supabase-js. Finders post items; people who lost something file a claim with `supabase.from('claims').insert({ item_id, claimant_id, message }).select()`. Finders answer with `.update({ status }).eq('id', id).select()`.

R1. Signed-in users can see every item. Finders can post items as themselves (always `open`) and change their own items.
R2. Claimants can see their own claims; finders can see every claim on their items.
R3. Users can claim open items they did not find, as themselves; new claims are always `pending`.
R4. Only the finder can approve or reject a pending claim on their item, and an item can have at most one approved claim. Claimants can never change a claim's status, and nothing else about a claim can change.
R5. Anonymous visitors cannot see or change anything.
R6. Server-side code using the service role keeps full access.

RLSBENCH-CANARY-f9002c750838f00b
