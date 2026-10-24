A property-search site built with supabase-js. Users save searches with `supabase.from('saved_searches').insert({...}).select()` and edit them with `.update({...}).eq('id', id).select()`. When `notify_email` is set, a server job emails new matches to that address. Supabase puts the account's verified email address in the JWT claim `email`; users can edit their `user_metadata`.

R1. Users can read, create, edit and delete only their own saved searches.
R2. `notify_email` must be empty or the user's own verified email address from the JWT `email` claim, ignoring upper and lower case. Nothing in `user_metadata` counts.
R3. Anonymous visitors cannot see or change saved searches.
R4. Server-side code using the service role keeps full access.

RLSBENCH-CANARY-f9002c750838f00b
