A portfolio site built with supabase-js and Supabase Storage. All files live in the bucket `media`, under the uploader's folder: `<user id>/public/<file>` for files shown on their public page and `<user id>/private/<file>` for everything else (sub-folders are allowed below these). The bucket `internal` is used only by server jobs. Uploads, renames and moves read the object row back.

R1. Anyone, including anonymous visitors, can read objects in `media` whose path is `<user id>/public/...`.
R2. Signed-in users can read every object under their own folder in `media`, public or private.
R3. Users can upload, rename or move, and delete objects only under their own folder in `media`. An object they upload or change always has `owner` set to themselves, and can never end up in someone else's folder.
R4. Objects in `internal`, and objects in `media` that are not under a user's folder, are visible only to server-side code.
R5. Anonymous visitors cannot upload, change or delete anything.
R6. Server-side code using the service role keeps full access.

RLSBENCH-CANARY-f9002c750838f00b
