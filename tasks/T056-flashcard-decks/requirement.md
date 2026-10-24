A flashcard app built with supabase-js. Decks belong to an owner and can be public. Cards are added with `supabase.from('cards').insert({ deck_id, front, back }).select()` and edited with `.update({...}).eq('id', id).select()`.

R1. Anyone, including anonymous visitors, can read public decks and their cards. Owners can also read their own private decks and cards.
R2. Signed-in users can create decks as their owner, and owners can edit and delete their own decks.
R3. Owners can add, edit and delete cards in their own decks. A card can never be moved into a deck that someone else owns.
R4. Anonymous visitors cannot create or change anything.
R5. Server-side code using the service role keeps full access.

RLSBENCH-CANARY-f9002c750838f00b
