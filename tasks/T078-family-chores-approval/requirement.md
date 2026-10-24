A family chores app built with supabase-js. Parents create chores with `supabase.from('chores').insert({...}).select()`. Children mark a chore done, and parents approve it, with `.update({...}).eq('id', id).select()`, which sends every field of the chore.

R1. Household members can see their household, its members and all of its chores.
R2. Parents can create chores in their household for its children (always `todo`), and can edit and delete their household's chores that are not yet approved. Chores can only be assigned to children of the same household.
R3. Children can mark their own `todo` chores as `done`, and nothing else: they cannot change a chore's title, points or assignee, or approve chores.
R4. Parents can approve chores in their household. Once a chore is approved, nobody can change or delete it.
R5. Nobody can change households or memberships through the app.
R6. Anonymous visitors cannot see or change anything.
R7. Server-side code using the service role keeps full access.

RLSBENCH-CANARY-f9002c750838f00b
