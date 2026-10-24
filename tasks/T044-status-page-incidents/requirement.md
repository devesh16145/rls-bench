A public status page built with supabase-js. Visitors load incidents with `supabase.from('incidents').select('*, incident_updates(*)')`. The on-call team writes incidents and updates from an internal tool that uses the service role; drafts stay unpublished until reviewed.

R1. Anyone, including anonymous visitors, can read published incidents.
R2. Anyone, including anonymous visitors, can read updates that are published and belong to a published incident.
R3. Unpublished incidents and updates are visible only to server-side code.
R4. Nobody can create, change or delete incidents or updates through the app.
R5. Server-side code using the service role keeps full access.

RLSBENCH-CANARY-f9002c750838f00b
