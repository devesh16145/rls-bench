A newsroom tool built with supabase-js. Writers create drafts with `supabase.from('articles').insert({...}).select()`, edit them, and submit them with `.update({ status: 'in_review' }).eq('id', id).select()`. Editors (users in `editors`) publish with `.update({ status: 'published', published_at }).eq('id', id).select()` or send articles back to `draft`.

R1. Anyone, including anonymous visitors, can read published articles. Writers can also read their own articles, and editors can read every article.
R2. Writers can create drafts as themselves, edit their own drafts, and submit them for review. They cannot edit an article once it is submitted, and cannot publish.
R3. Editors can edit articles that are in review, publish them, or send them back to `draft`. Editors cannot change drafts or published articles.
R4. Once published, an article can no longer be changed through the app. Writers can delete only their own drafts.
R5. Users can see whether they themselves are an editor. Nobody can change `editors` through the app.
R6. Server-side code using the service role keeps full access.

RLSBENCH-CANARY-f9002c750838f00b
