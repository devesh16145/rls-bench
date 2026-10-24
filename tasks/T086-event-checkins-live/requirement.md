An event app built with supabase-js. Attendees scan a QR code that runs `supabase.from('checkins').insert({ event_id, user_id }).select()`; `checked_in_at` defaults to the current time. An event is live from `starts_at` to `ends_at`, compared with `now()`.

R1. Signed-in users can see every event and their own check-ins.
R2. Users can check themselves in, once per event, only while the event is live.
R3. `checked_in_at` is always the time of check-in: users can never set it. Check-ins cannot be changed or deleted through the app.
R4. Anonymous visitors cannot see or change anything.
R5. Server-side code using the service role keeps full access.

RLSBENCH-CANARY-f9002c750838f00b
