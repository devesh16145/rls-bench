A wiki built with supabase-js. Saving a page sends every field: `supabase.from('pages').update({ title, body, is_protected, updated_by }).eq('slug', slug).select()`, then inserts a revision with `.from('page_revisions').insert({ slug, body, author_id }).select()`. Editors are the users listed in `editors`.

R1. Anyone, including anonymous visitors, can read pages and revisions. Signed-in users can see who the editors are.
R2. Signed-in users can create unprotected pages and edit unprotected pages, always recording themselves as `updated_by`. Editors can also create protected pages.
R3. Protected pages can be edited only by editors, and only editors can protect or unprotect a page.
R4. Users can add revisions, as their author, only for pages they are allowed to edit. Revisions are never changed or deleted, and pages are never deleted.
R5. Nobody can change `editors` through the app.
R6. Server-side code using the service role keeps full access.

RLSBENCH-CANARY-f9002c750838f00b
