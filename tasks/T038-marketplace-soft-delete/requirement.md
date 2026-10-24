A second-hand marketplace built with supabase-js. Sellers create listings with `.insert({...}).select()` and edit them with `.update({...}).eq('id', id)`. Listings are never hard-deleted: a seller removes one with `.update({ deleted_at }).eq('id', id)`. Moderators (users in `moderators`) flag listings that break the rules.

R1. Anyone, including anonymous visitors, can see listings that are active, not flagged and not deleted.
R2. Sellers can see all of their own listings, including drafts, flagged and deleted ones. Moderators can see every listing.
R3. Sellers can create listings as themselves, never flagged or deleted, and can edit their own listings that are not deleted, but can never flag or unflag a listing.
R4. Sellers remove their own listings by setting `deleted_at`. A deleted listing can no longer be changed by its seller.
R5. Moderators can change any listing, including flagging and unflagging it.
R6. Nobody can hard-delete listings or change `moderators` through the app.
R7. Server-side code using the service role keeps full access.

RLSBENCH-CANARY-f9002c750838f00b
