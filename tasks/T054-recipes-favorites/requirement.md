A recipe site built with supabase-js. Authors write recipes with `.insert({...}).select()` and edit them with `.update({...}).eq('id', id).select()`. Users save favourites with `supabase.from('favorites').insert({ user_id, recipe_id }).select()` and remove them with `.delete()`.

R1. Anyone, including anonymous visitors, can read public recipes. Authors can also read their own private recipes.
R2. Signed-in users can create recipes as their author, and authors can edit and delete their own recipes. A recipe can never be given to another author.
R3. Users can see only their own favourites.
R4. Users can add favourites, as themselves, only for recipes they can read, and can remove their own favourites.
R5. Anonymous visitors cannot create or change anything.
R6. Server-side code using the service role keeps full access.

RLSBENCH-CANARY-f9002c750838f00b
