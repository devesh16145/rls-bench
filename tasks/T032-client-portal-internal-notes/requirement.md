An agency's client portal built with supabase-js. Staff are the users listed in `staff`; each project belongs to one client. Comments are posted with `supabase.from('project_comments').insert({ project_id, author_id, body, is_internal }).select()` and edited with `.update({...}).eq('id', id).select()`. Internal comments are notes for staff only.

R1. Clients can see their own projects. Staff can see every project.
R2. Clients can read the comments on their own projects that are not internal. Staff can read every comment.
R3. Clients can comment, as themselves, on their own projects, and their comments are never internal. Staff can comment, as themselves, on any project, internal or not.
R4. Authors can edit and delete their own comments, within the same limits as when posting.
R5. Users can see whether they themselves are staff. Nobody can change `staff` or projects through the app.
R6. Anonymous visitors cannot see or change anything.
R7. Server-side code using the service role keeps full access.

RLSBENCH-CANARY-f9002c750838f00b
