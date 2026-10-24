A billing app built with supabase-js and Supabase Storage. Each user's invoices live in the private bucket `invoices` under `<user id>/<file>.pdf`. The app uploads with `supabase.storage.from('invoices').upload(path, file)`, which inserts the object row with `owner` set to the uploader. Uploads, renames and moves read the object row back.

R1. Users can read only the objects in their own folder (`<their user id>/...`) of `invoices`.
R2. Users can upload, rename and delete objects only within their own folder, and only files whose name ends in `.pdf`. Objects they upload or change always have `owner` set to themselves.
R3. Objects outside users' folders are visible only to server-side code.
R4. Anonymous visitors cannot see or change anything.
R5. Server-side code using the service role keeps full access.

RLSBENCH-CANARY-f9002c750838f00b
