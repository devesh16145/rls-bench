A bike-share app built with supabase-js. Riders start a rental with `supabase.from('rentals').insert({ bike_id, user_id }).select()` and end it with `supabase.from('rentals').update({ returned_at }).eq('id', id).select()`. A server job computes `cost_cents` after the return. Staff are the users in `staff`.

R1. Signed-in users can see every bike. Users can see their own rentals; staff can see all rentals.
R2. A rider can start a rental as themselves only for a bike that is in service and not currently rented, and only if they have no open rental of their own. A new rental is open (no return time).
R3. A rider ends their own open rental by setting its return time. Riders can never write or change the cost, and nothing else about a rental changes through the app; rentals are never deleted by users.
R4. Staff can change a bike's status. Nobody else can change bikes, and nobody can change who is staff. Users can see their own staff row.
R5. Anonymous visitors cannot see or change anything. Server-side code using the service role keeps full access.

RLSBENCH-CANARY-f9002c750838f00b
