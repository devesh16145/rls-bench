A co-working space app built with supabase-js. Members book a desk for a day with `supabase.from('bookings').insert({ desk_id, day, user_id }).select()` and cancel with `.delete()`; the primary key prevents double bookings. Dates are compared with `current_date`.

R1. Signed-in users can see every desk and every booking (to check availability), and their own membership.
R2. Members can book desks, as themselves, for today or a later day, but no later than their membership's `valid_until`. Premium desks can be booked only by premium members.
R3. A member can hold at most 3 upcoming bookings (today or later) at a time.
R4. Members can cancel their own upcoming bookings. Past bookings cannot be changed or deleted, and bookings are never edited.
R5. Nobody can change desks or memberships through the app. Anonymous visitors cannot see or change anything.
R6. Server-side code using the service role keeps full access.

RLSBENCH-CANARY-f9002c750838f00b
