A conference call-for-papers app built with supabase-js. Speakers submit with `supabase.from('proposals').insert({...}).select()`. Reviewers (users in `reviewers`) score with `supabase.from('reviews').insert({ proposal_id, reviewer_id, score, comment }).select()`. The programme committee records decisions from a server tool using the service role.

R1. Speakers can see their own proposals; reviewers can see every proposal.
R2. Signed-in users can submit proposals as themselves (always `submitted`) and edit their own proposals while they are undecided.
R3. Reviewers can review each undecided proposal once, as themselves, but never their own proposals, and can edit their own reviews while the proposal is undecided.
R4. Reviewers see only their own reviews, so reviews stay independent. Speakers can see the reviews of their own proposals only once a decision has been made.
R5. Decisions are made only by server-side code, and users can see whether they themselves are a reviewer. Nobody can change `reviewers` through the app.
R6. Anonymous visitors cannot see or change anything. Server-side code using the service role keeps full access.

RLSBENCH-CANARY-f9002c750838f00b
