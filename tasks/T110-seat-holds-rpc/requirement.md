A ticketing app. The seat map is read from the view `seat_map` (columns `id, event_id, label, status`), which must exist with that name. Seats are held and booked only through two RPCs that must exist: `hold_seat(p_seat_id bigint)` and `confirm_seat(p_seat_id bigint)`, both returning void and raising an error when the action is not allowed. Events and seats are created by server-side code.

R1. Signed-in users can read every event and the seat map. In the seat map a seat whose hold has expired shows as free; the map never shows who holds or booked a seat.
R2. A user can read rows of `seats` only for seats they hold or booked themselves.
R3. `hold_seat` holds a seat for the caller for 10 minutes if the seat is free or its current hold has expired; otherwise it fails. A hold records the caller as holder.
R4. `confirm_seat` books a seat for the caller only if the caller holds it with a hold that has not expired; otherwise it fails. Booking records the caller and clears the hold.
R5. Seats are never created, changed or deleted directly through the app, only through the two RPCs.
R6. Anonymous visitors cannot read the seat map or call the RPCs. Server-side code using the service role keeps full access.

RLSBENCH-CANARY-f9002c750838f00b
