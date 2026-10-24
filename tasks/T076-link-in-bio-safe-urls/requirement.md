A link-in-bio site built with supabase-js. Each user's public page lists their visible links. Owners add links with `supabase.from('bio_links').insert({...}).select()` and edit them with `.update({...}).eq('id', id).select()`. Pages render `url` directly as an anchor `href`.

R1. Anyone, including anonymous visitors, can read visible links. Owners can also read their own hidden links.
R2. Signed-in users can add links as themselves, and owners can edit, hide and delete their own links.
R3. Every link's `url` must start with `https://` (lowercase), both when it is added and after every edit, so pages never contain `javascript:` or plain `http://` links.
R4. Anonymous visitors cannot add or change links.
R5. Server-side code using the service role keeps full access.

RLSBENCH-CANARY-f9002c750838f00b
