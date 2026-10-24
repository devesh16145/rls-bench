An online-course platform built with supabase-js. Courses belong to an instructor (`instructor_id`) and have lessons; a lesson can be marked as a free preview. Students enroll themselves with `supabase.from('enrollments').insert({ course_id, student_id }).select()`; other writes also read the written row back with `.select()`.

R1. Anyone, including anonymous visitors, can read published courses. Instructors can also read their own unpublished courses.
R2. Signed-in users can create courses as their instructor, and instructors can edit and delete their own courses. A course can never be handed to another instructor.
R3. Anyone can read the preview lessons of published courses. Students enrolled in a published course can read all its lessons. Instructors can read, create, edit and delete every lesson of their own courses.
R4. Signed-in users can enroll themselves in published courses and remove their own enrollments. Nobody can enroll someone else.
R5. Students can see their own enrollments, and instructors can see the enrollments in their courses.
R6. Anonymous visitors cannot change anything.
R7. Server-side code using the service role keeps full access.

RLSBENCH-CANARY-f9002c750838f00b
