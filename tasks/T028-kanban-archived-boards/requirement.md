A kanban app built with supabase-js. Board members are viewers or editors. Cards are created with `supabase.from('cards').insert({...}).select()` and moved or edited with `.update({...}).eq('id', id).select()`.

R1. Members can see the boards they belong to and every member of those boards.
R2. Members can read all cards on their boards.
R3. Editors can create, edit, move between columns and delete cards on their boards. A card can only end up on a board where the user is an editor.
R4. Viewers cannot create, change or delete cards.
R5. Archived boards are read-only: nobody can create, change or delete cards on an archived board, not even its editors.
R6. Boards and memberships cannot be changed through the app.
R7. Anonymous visitors cannot see or change anything.
R8. Server-side code using the service role keeps full access.

RLSBENCH-CANARY-f9002c750838f00b
