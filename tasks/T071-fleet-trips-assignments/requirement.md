A fleet app built with supabase-js. Fleet managers (users in `fleet_managers`) assign drivers to vehicles for date ranges; both `starts_on` and `ends_on` are included. Drivers log trips with `supabase.from('trips').insert({ vehicle_id, driver_id, trip_date, km }).select()` and correct them with `.update({...}).eq('id', id).select()`.

R1. Signed-in users can see every vehicle. Drivers can see their own assignments and trips; fleet managers can see every assignment and trip.
R2. Drivers can log trips, as themselves, only for a vehicle and a date covered by one of their own assignments, including the first and last day.
R3. Drivers can edit and delete their own trips; an edited trip must still be covered by one of their assignments.
R4. Only fleet managers can create, change or delete assignments. Nobody can change `fleet_managers` through the app.
R5. Anonymous visitors cannot see or change anything.
R6. Server-side code using the service role keeps full access.

RLSBENCH-CANARY-f9002c750838f00b
