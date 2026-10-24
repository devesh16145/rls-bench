An apartment-community app built with supabase-js. Residents register cars with `supabase.from('permits').insert({ unit_id, plate, valid_until }).select()` and update the plate with `.update({ plate }).eq('id', id)`. HOA admins (users in `hoa_admins`) revoke permits with `.update({ revoked: true }).eq('id', id)`. A permit is active while it is not revoked and `valid_until` is today or later (compared with `current_date`).

R1. Residents can see their own residence rows and the permits of their unit. HOA admins can see every permit.
R2. Residents can add permits for their own unit while it has fewer than 2 active permits. A new permit is never revoked and is valid for at most 365 days from today.
R3. Residents can change the plate on their unit's permits, but cannot change validity or revoke or un-revoke permits.
R4. HOA admins can revoke any permit; nobody can un-revoke a permit. Permits are never deleted.
R5. Nobody can change residents or HOA admins through the app. Anonymous visitors cannot see or change anything.
R6. Server-side code using the service role keeps full access.

RLSBENCH-CANARY-f9002c750838f00b
