A course discussion forum built with supabase-js. Course members are students or teaching assistants (TAs). Threads and posts are created with `.insert({...}).select()` and edited with `.update({...}).eq('id', id).select()`.

R1. Course members can see their courses, their own enrollment rows, and every thread and post in their courses.
R2. Course members can start unlocked threads and write posts, as themselves, in the unlocked threads of their courses.
R3. Authors can edit and delete their own posts, but only while the thread is unlocked.
R4. TAs can lock and unlock the threads of their courses and delete any post in them. Students cannot lock or unlock threads, not even their own.
R5. Nobody can change courses or enrollments through the app.
R6. Anonymous visitors cannot see or change anything.
R7. Server-side code using the service role keeps full access.

RLSBENCH-CANARY-f9002c750838f00b
