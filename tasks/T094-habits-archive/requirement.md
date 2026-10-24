A habit tracker built with supabase-js. The main list loads `supabase.from('habits').select().is('archived_at', null)` and the archive page loads the rest. Users archive a habit with `.update({ archived_at })` and restore it with `.update({ archived_at: null })`, each `.eq('id', id)`.

R1. Users can see all of their own habits, both active and archived, and nobody else's.
R2. Users can create habits as themselves and edit, archive (set `archived_at`), restore (clear `archived_at`) and delete their own habits.
R3. Anonymous visitors cannot see or change anything.
R4. Server-side code using the service role keeps full access.

RLSBENCH-CANARY-f9002c750838f00b
