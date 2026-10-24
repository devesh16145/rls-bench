A tutoring marketplace built with supabase-js. Bookings between a student and a tutor are created and confirmed by the server. The booking page sends messages with `supabase.from('booking_messages').insert({ booking_id, sender_id, body }).select()`.

R1. Students and tutors can see their own bookings and every message on them.
R2. The student and tutor of a booking can send messages on it, as themselves, but only while the booking is confirmed.
R3. Senders can delete their own messages. Nobody can edit messages.
R4. Nobody can create or change bookings through the app. Anonymous visitors cannot see or change anything.
R5. Server-side code using the service role keeps full access.

RLSBENCH-CANARY-f9002c750838f00b
