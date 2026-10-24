A community notice board built with supabase-js. Users post with `supabase.from('board_notes').insert({ author_id, body, color }).select()` and edit with `.update({ body, color }).eq('id', id).select()`. Moderators pin notes from an admin tool that uses the service role.

R1. Anyone, including anonymous visitors, can read every note.
R2. Signed-in users can post notes as themselves, and authors can edit and delete their own notes.
R3. Only moderators pin and unpin notes. Users can never set or change `is_pinned`, not even on their own notes, and editing a pinned note keeps it pinned.
R4. Anonymous visitors cannot post or change anything.
R5. Server-side code using the service role keeps full access.

RLSBENCH-CANARY-f9002c750838f00b
