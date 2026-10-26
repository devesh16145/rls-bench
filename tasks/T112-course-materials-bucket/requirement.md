A course site using Supabase Storage. Files live in the private bucket `materials` under a folder named after the course id (`<course_id>/<file>`). Instructors upload from the app with the storage client, which inserts `storage.objects` rows with `owner` set to the uploading user. The bucket `avatars` belongs to another feature and is out of scope except that nothing here may touch it.

R1. The instructor of a course can upload files into that course's folder in `materials`, as the owner of the file, and only PDF (`.pdf`) or MP4 (`.mp4`) files. They can rename and delete the files in their course's folder; a file never moves to another course's folder.
R2. Students enrolled in a course can read that course's files. Nobody else can read a course's files.
R3. Nobody uploads anywhere else in `materials` (outside a course folder they teach), and nothing in other buckets is readable or changeable through these rules.
R4. Signed-in users can read every course; students can see their own enrollments. Nobody changes courses or enrollments through the app.
R5. Anonymous visitors cannot see or change anything. Server-side code using the service role keeps full access.

RLSBENCH-CANARY-f9002c750838f00b
