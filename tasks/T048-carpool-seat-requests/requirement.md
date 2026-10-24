A car-pooling app built with supabase-js. Passengers request a seat with `supabase.from('ride_bookings').insert({ ride_id, passenger_id }).select()` and withdraw with `.delete()`. Drivers answer with `.update({ status }).match({ ride_id, passenger_id }).select()`. Departure times are compared with `now()`.

R1. Signed-in users can see every ride. Drivers can create rides as themselves and edit and delete their own rides.
R2. Passengers can see their own bookings; drivers can see every booking on their rides.
R3. Signed-in users can request a seat, as themselves, on rides that have not departed and that they are not driving. New requests are always `requested`. Passengers can withdraw their own bookings before departure.
R4. Only the driver can confirm or decline requests on their ride, and only before departure. A request can be confirmed only while the ride has fewer confirmed bookings than seats. Nothing else about a booking can change.
R5. Anonymous visitors cannot see or change anything.
R6. Server-side code using the service role keeps full access.

RLSBENCH-CANARY-f9002c750838f00b
