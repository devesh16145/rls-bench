A note-taking app. Each note belongs to the user in `user_id`. A note's author can mark it public with `is_public`.

R1. Signed-in users can read their own notes.
R2. Signed-in users can also read notes that other users marked public. Anonymous visitors cannot read public notes.
R3. Users can create notes only as themselves.
R4. Users can edit and delete only their own notes, and cannot hand a note over to another user.
R5. Anonymous visitors cannot read, create, edit or delete any notes.
R6. Server-side code using the service role keeps full access.

RLSBENCH-CANARY-f9002c750838f00b
