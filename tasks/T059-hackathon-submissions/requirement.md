A hackathon platform built with supabase-js. Each team has one submission, saved with `supabase.from('submissions').upsert({ team_id, repo_url, notes }).select()`. Deadlines are compared with `now()`.

R1. Signed-in users can see every event and team. Users can see their own team memberships.
R2. Team members can see their own team's submission. Judges can see the submissions of their event, but only once its deadline has passed.
R3. Team members can create and edit their own team's submission until the event's deadline.
R4. After the deadline nobody can change submissions through the app, and submissions are never deleted.
R5. Nobody can change events, teams, memberships or judges through the app.
R6. Anonymous visitors cannot see or change anything.
R7. Server-side code using the service role keeps full access.

RLSBENCH-CANARY-f9002c750838f00b
