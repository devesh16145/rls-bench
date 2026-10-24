A company document archive built with supabase-js. Uploads use `.insert({...}).select()`, renames `.update({ name }).eq('id', id).select()`, and deletes `.delete().eq('id', id)`. The legal team places and lifts legal holds from a server tool that uses the service role.

R1. Users can see their own files. Org admins (users in `org_admins`) can see every file.
R2. Users can upload files as themselves, and rename and delete their own files. Org admins can rename and delete any file.
R3. A file under legal hold cannot be renamed or deleted by anyone through the app, including its owner and org admins.
R4. Nobody can place or lift a legal hold through the app.
R5. Nobody can change `org_admins` through the app.
R6. Anonymous visitors cannot see or change anything.
R7. Server-side code using the service role keeps full access, including legal holds.

RLSBENCH-CANARY-f9002c750838f00b
