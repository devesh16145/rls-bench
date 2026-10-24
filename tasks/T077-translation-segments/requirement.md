A translation tool built with supabase-js. Segments are created by a server import (service role). Translators save with `supabase.from('segments').update({ target_text, translated_by }).eq('id', id).select()`; reviewers approve with `.update({ status: 'reviewed' }).eq('id', id).select()`. People are assigned per project and language in `translators`.

R1. Users can see the projects they work on, their own assignment rows, and the segments of the languages they are assigned to.
R2. Translators can edit the translation of draft segments in their language, always recording themselves in `translated_by`.
R3. Reviewers of a language can mark its draft segments `reviewed` (and may correct the translation). Translators cannot mark segments reviewed.
R4. Reviewed segments can no longer be changed by anyone through the app. Nobody can change a segment's source text, and segments are never created or deleted through the app.
R5. Anonymous visitors cannot see or change anything.
R6. Server-side code using the service role keeps full access.

RLSBENCH-CANARY-f9002c750838f00b
