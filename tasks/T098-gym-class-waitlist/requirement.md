A gym's class-booking app built with supabase-js. Members join with `supabase.from('class_spots').insert({ class_id, user_id, status }).select()`, choosing `enrolled` or `waitlisted`; a waitlisted member moves up with `.update({ status: 'enrolled' }).match({ class_id, user_id }).select()` and leaves with `.delete()`.

R1. Signed-in users can see every class. Members can see their own spots; instructors can see every spot in the classes they teach.
R2. Members can join a class as themselves: as `enrolled` only while the class has fewer enrolled members than its capacity, otherwise only as `waitlisted`.
R3. Members can move their own waitlisted spot to `enrolled` only when there is room, and can leave a class by deleting their own spot. Nothing else about a spot can change.
R4. Instructors can remove any spot from the classes they teach.
R5. Nobody can change classes through the app. Anonymous visitors cannot see or change anything.
R6. Server-side code using the service role keeps full access.

RLSBENCH-CANARY-f9002c750838f00b
