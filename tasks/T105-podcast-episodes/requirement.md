A podcast site built with supabase-js. Shows and their hosts (`hosts`) are set up by server-side code. Hosts manage episodes with `supabase.from('episodes').insert({...}).select()` and `.update({...}).eq('id', id).select()`. Visitors, signed in or not, browse the site.

R1. Anyone, including anonymous visitors, can read every show and every published episode whose publish time has passed.
R2. The hosts of a show can read all of that show's episodes, including drafts and episodes dated in the future.
R3. A host can create episodes for the shows they host, as themselves, and can edit those episodes; an episode must always belong to a show its editor hosts.
R4. A host can delete a draft episode of their show. Published episodes are never deleted through the app.
R5. Signed-in users can see their own host rows. Nobody can change shows or hosts through the app.
R6. Anonymous visitors cannot change anything. Server-side code using the service role keeps full access.

RLSBENCH-CANARY-f9002c750838f00b
