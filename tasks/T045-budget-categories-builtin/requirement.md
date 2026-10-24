A budgeting app built with supabase-js. Built-in categories have no `user_id` and are shared by everyone. Users add their own with `supabase.from('categories').insert({ user_id, name, color }).select()` and edit them with `.update({...}).eq('id', id).select()`.

R1. Signed-in users can read the built-in categories and their own categories.
R2. Users can create categories only for themselves, and can edit and delete only their own categories.
R3. Built-in categories cannot be created, changed or deleted through the app, and a user's category can never be turned into a built-in one.
R4. Anonymous visitors cannot see or change any categories.
R5. Server-side code using the service role keeps full access.

RLSBENCH-CANARY-f9002c750838f00b
