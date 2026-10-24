An email client built with supabase-js. Users write drafts with `supabase.from('emails').insert({...}).select()` and edit them with `.update({...}).eq('id', id).select()`. A server job sends drafts and records the time in `sent_at`, using the service role.

R1. Users can read their own emails, drafts and sent.
R2. Users can create drafts (no `sent_at`) as themselves, and can edit and delete their own drafts.
R3. Once an email has been sent, nobody can change or delete it through the app, and users can never set `sent_at` themselves.
R4. Anonymous visitors cannot see or change anything.
R5. Server-side code using the service role keeps full access.

RLSBENCH-CANARY-f9002c750838f00b
