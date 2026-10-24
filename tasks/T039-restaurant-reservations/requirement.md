A restaurant-booking app built with supabase-js. Guests book with `supabase.from('reservations').insert({ restaurant_id, user_id, reserved_for, party_size }).select()` and cancel with `.update({ status: 'cancelled' }).eq('id', id).select()`. Staff record what happened with `.update({ status }).eq('id', id).select()`. Times are compared with the database clock, `now()`.

R1. Signed-in users can see the list of restaurants. Guests can see their own reservations; restaurant staff can see every reservation at their restaurant.
R2. Guests can book, as themselves, only for a time in the future, and new reservations are always `booked`.
R3. Guests can cancel their own `booked` reservations while the reservation time is still in the future. Guests cannot change anything else.
R4. Staff can mark `booked` reservations at their restaurant as `seated` or `no_show`, but only once the reservation time has passed. Staff cannot change anything else.
R5. Restaurants and staff lists cannot be changed through the app, and reservations are never deleted.
R6. Anonymous visitors cannot see or change anything.
R7. Server-side code using the service role keeps full access.

RLSBENCH-CANARY-f9002c750838f00b
