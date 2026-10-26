A volunteer scheduling app built with supabase-js. Coordinators are the users listed in `coordinators`. Volunteers sign up with `supabase.from('signups').insert({ shift_id, volunteer_id }).select()` and cancel with `supabase.from('signups').update({ status: 'cancelled' }).eq('id', id).select()`.

R1. Signed-in users can see every shift that is not cancelled. Coordinators can see all shifts, including cancelled ones.
R2. A volunteer can sign up as themselves for a shift that is open, starts in the future and still has room (fewer active sign-ups than its capacity), and at most once per shift at a time. New sign-ups are always active.
R3. Volunteers can see their own sign-ups; coordinators can see every sign-up.
R4. A volunteer can cancel their own active sign-up by setting its status to cancelled. Nothing else about a sign-up can be changed through the app, and sign-ups are never deleted.
R5. Coordinators can create shifts as themselves and can edit or cancel any shift. Nobody else can create or change shifts, and nobody can change who is a coordinator.
R6. Anonymous visitors cannot see or change anything. Server-side code using the service role keeps full access.

RLSBENCH-CANARY-f9002c750838f00b
