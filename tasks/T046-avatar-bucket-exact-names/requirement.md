A community app built with supabase-js and Supabase Storage. Each user's profile picture is stored in the bucket `avatars` at the top level, named `<user id>.png` or `<user id>.jpg`. The app uploads with `supabase.storage.from('avatars').upload(name, file, { upsert: true })`, which inserts or updates the object row and reads it back. The bucket `docs` is used only by server jobs.

R1. Anyone, including anonymous visitors, can read objects in `avatars`.
R2. Signed-in users can upload, replace and delete only the objects in `avatars` named exactly `<their user id>.png` or `<their user id>.jpg` (no folders), with `owner` set to themselves.
R3. Objects in other buckets cannot be read or written through the app.
R4. Anonymous visitors cannot upload, change or delete anything.
R5. Server-side code using the service role keeps full access.

RLSBENCH-CANARY-f9002c750838f00b
