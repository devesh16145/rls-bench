A calendar app built with supabase-js. Each event sits on its owner's calendar (`owner_id`). Calendar owners can delegate their calendar to assistants through `delegations`; a delegation may allow editing and may expire at `expires_at` (no value means it never expires). Events are created with `.insert({...}).select()` and edited with `.update({...}).eq('id', id).select()`, so written rows are read back immediately.

R1. Users can create, read, edit and delete events on their own calendar.
R2. An event can never be moved to another calendar: `owner_id` never changes.
R3. A user holding an unexpired delegation can read the grantor's events that are not private. If the delegation allows editing, they can also create, edit and delete the grantor's non-private events, but can never create private events or make an event private.
R4. Private events are never visible to delegates in `events`. Provide a view `public.busy_slots` with exactly the columns `owner_id`, `starts_at` and `ends_at` that lists every event (private or not) on the viewer's own calendar and on the calendars they hold an unexpired delegation for, and nothing else.
R5. Calendar owners can create, change and remove delegations of their own calendar. Delegates can see the delegations given to them. Nobody can create or change delegations of a calendar that isn't theirs, so delegates cannot pass access on.
R6. Anonymous visitors cannot see or change anything, including `busy_slots`.
R7. Server-side code using the service role keeps full access, including to `busy_slots`.

RLSBENCH-CANARY-f9002c750838f00b
