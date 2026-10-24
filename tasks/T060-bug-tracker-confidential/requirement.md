An issue tracker built with supabase-js. Project members are reporters, developers or maintainers. Issues are filed with `supabase.from('issues').insert({...}).select()` and updated with `.update({...}).eq('id', id).select()`. Confidential issues hold security reports.

R1. Members can see their projects and every member of those projects.
R2. Members can see every non-confidential issue in their projects. A confidential issue is visible only to the project's maintainers, its reporter and its assignee.
R3. Members can file issues in their projects as the reporter, confidential or not; new issues are always `open`.
R4. Developers and maintainers can update the issues they can see. Only maintainers can make an issue confidential or not confidential. Reporters cannot update issues.
R5. Issues are never deleted, and nobody can change projects or memberships through the app.
R6. Anonymous visitors cannot see or change anything.
R7. Server-side code using the service role keeps full access.

RLSBENCH-CANARY-f9002c750838f00b
