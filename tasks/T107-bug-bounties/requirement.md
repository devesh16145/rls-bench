A bug-bounty board built with supabase-js. Users post bounties with `supabase.from('bounties').insert({...}).select()`, submit findings with `supabase.from('submissions').insert({ bounty_id, submitter_id, body }).select()`, and the poster awards a bounty with `supabase.from('bounties').update({ status: 'awarded', awarded_submission_id }).eq('id', id).select()`.

R1. Signed-in users can read every bounty.
R2. Signed-in users can post bounties as themselves. A new bounty is open and has no award.
R3. A user can submit to an open bounty as themselves, never to their own bounty, and at most once per bounty.
R4. Submitters can see their own submissions. The poster of a bounty can see every submission to it. Nobody else can see a submission.
R5. A submitter can edit the text of their own submission while the bounty is open. Nothing else about a submission changes through the app, and submissions are never deleted.
R6. The poster awards their bounty exactly once, by marking it awarded with one of that bounty's own submissions, and only while it is open; afterwards nothing about the bounty changes. Nobody else can change a bounty.
R7. Anonymous visitors cannot see or change anything. Server-side code using the service role keeps full access.

RLSBENCH-CANARY-f9002c750838f00b
