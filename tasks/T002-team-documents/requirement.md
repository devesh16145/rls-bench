A document workspace. Users belong to teams through `team_members`, each with the role `viewer` or `editor`. Every document belongs to one team. A document is deleted when `deleted_at` is set.

R1. Users can see the teams they belong to.
R2. Users can see their own membership rows (which teams they are in and with what role), but not other people's.
R3. Members of a team can read the team's documents, except deleted documents, which are hidden from every user of the app.
R4. Editors can create documents in their teams, always recorded as created by themselves. Viewers cannot create documents.
R5. Editors can edit any document in their teams. After an edit, the document must still belong to a team where the user is an editor.
R6. Only the person who created a document can delete it.
R7. Teams and memberships cannot be created, changed or removed by users of the app.
R8. Anonymous visitors cannot see or change anything.
R9. Server-side code using the service role keeps full access.

RLSBENCH-CANARY-f9002c750838f00b
