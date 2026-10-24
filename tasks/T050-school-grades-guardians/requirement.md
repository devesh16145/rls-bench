A school app built with supabase-js. Teachers record grades with `supabase.from('grades').insert({...}).select()` and correct them with `.update({...}).eq('id', id).select()`. `guardians` links parents to their children.

R1. Students can read their own grades. Guardians can read the grades of the students they are guardians of. Teachers can read every grade in the classes they teach.
R2. Teachers can add, change and delete grades in the classes they teach, only for students enrolled in that class, with themselves as `graded_by`.
R3. Students and guardians cannot add, change or delete grades.
R4. Signed-in users can see the class list. Students can see their own enrollments and teachers the rosters of their classes; users can see the guardian links that involve them. Nobody can change classes, enrollments or guardian links through the app.
R5. Anonymous visitors cannot see or change anything.
R6. Server-side code using the service role keeps full access.

RLSBENCH-CANARY-f9002c750838f00b
