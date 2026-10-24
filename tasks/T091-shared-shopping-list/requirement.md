A household shopping-list app built with supabase-js. Members add items with `supabase.from('shopping_items').insert({ household_id, name, added_by }).select()`. They claim an item ("I'll buy it") with `.update({ claimed_by: userId })`, unclaim with `.update({ claimed_by: null })` and tick it off with `.update({ is_bought: true })`, each `.eq('id', id).select()`.

R1. Members can see their household's members and all of its items.
R2. Members can add items to their household as themselves; new items are unclaimed and not bought.
R3. Members can claim an unclaimed item for themselves and unclaim items they claimed. Nobody can claim on someone else's behalf or take an item someone else has claimed.
R4. Only the member who claimed an item can mark it bought, and a bought item stays claimed. Nothing else about an item can change.
R5. The member who added an item can delete it while it is not bought.
R6. Anonymous visitors cannot see or change anything. Server-side code using the service role keeps full access.

RLSBENCH-CANARY-f9002c750838f00b
