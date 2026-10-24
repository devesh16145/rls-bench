A project-management app. Organizations have members, each with the role `admin` or `member`. Projects belong to one organization. Project files live in the Supabase Storage bucket `project-files` at the path `<project id>/<file name>`. Profile pictures live in the public bucket `avatars` at the path `<user id>/<file name>`.

R1. Members of an organization can see every membership row of that organization (who belongs and with what role), and nothing about the membership of organizations they don't belong to.
R2. Members can see the organizations they belong to and those organizations' projects.
R3. Only organization admins can create, rename or delete projects, and only within organizations they administer. Admin status comes only from organization membership; nothing in the user's token or user metadata grants it.
R4. Members of an organization can read the files of its projects. Only admins of that organization can upload or delete project files.
R5. Anyone, including anonymous visitors, can view avatars. Signed-in users can upload avatars only into the folder named with their own user id.
R6. Memberships cannot be created, changed or removed by users of the app.
R7. Anonymous visitors cannot see or change anything else.
R8. Server-side code using the service role keeps full access.

RLSBENCH-CANARY-f9002c750838f00b
