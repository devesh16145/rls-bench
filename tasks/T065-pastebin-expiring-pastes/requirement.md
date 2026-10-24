A pastebin built with supabase-js. Anyone can create a paste with `supabase.from('pastes').insert({ content, is_private, expires_at })`; `author_id` defaults to `auth.uid()`, so anonymous pastes have no author. A paste with no `expires_at` never expires; expiry is compared with `now()`.

R1. Anyone, including anonymous visitors, can read pastes that are neither private nor expired.
R2. Signed-in authors can also read their own private and expired pastes.
R3. Anyone can create pastes. A paste's `author_id` is always its creator when signed in and empty when anonymous, and anonymous pastes can never be private.
R4. Authors can delete their own pastes. Nobody can edit pastes, and pastes without an author can only be removed by server-side code.
R5. Server-side code using the service role keeps full access.

RLSBENCH-CANARY-f9002c750838f00b
