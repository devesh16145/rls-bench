A personal website's guestbook built with supabase-js. Visitors sign it with `supabase.from('guestbook_entries').insert({ display_name, message })` and do not read the row back. `author_id` defaults to `auth.uid()`, so signed-in visitors' entries record their user id and anonymous entries have no author. The site owner moderates in an admin tool that uses the service role.

R1. Anyone, including anonymous visitors, can read approved entries.
R2. Anyone can sign the guestbook. New entries are always unapproved, and their `author_id` is always the signer: their own user id when signed in, empty when anonymous.
R3. Signed-in visitors can also read and delete their own entries, approved or not. Entries without an author can only be removed by the site owner.
R4. Nobody can edit or approve entries through the app.
R5. Server-side code using the service role keeps full access.

RLSBENCH-CANARY-f9002c750838f00b
