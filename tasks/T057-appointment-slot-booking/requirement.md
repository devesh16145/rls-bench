A clinic booking app built with supabase-js. Providers' slots are created by a server tool using the service role. Patients book a slot with `supabase.from('slots').update({ booked_by: userId }).eq('id', slotId).select()` and cancel with `.update({ booked_by: null }).eq('id', slotId)`. Times are compared with `now()`.

R1. Signed-in users can see the list of providers.
R2. Patients can see open slots (not booked) that are in the future, and the slots they have booked. Providers can see all of their own slots, including who booked them.
R3. A patient can book an open future slot for themselves, never for someone else.
R4. A patient can cancel their own booking while the slot is still in the future.
R5. Nobody can create, move or delete slots, or change anything else about them, through the app.
R6. Anonymous visitors cannot see or change anything.
R7. Server-side code using the service role keeps full access.

RLSBENCH-CANARY-f9002c750838f00b
