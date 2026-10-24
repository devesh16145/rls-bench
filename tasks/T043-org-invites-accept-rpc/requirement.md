A team app built with supabase-js. Admins invite people by email; the invite link contains a secret token, and the invitee joins by calling `supabase.rpc('accept_invite', { p_token })`. Implement it as `public.accept_invite(p_token text) returns bigint`, returning the organization's id. Supabase puts the account's verified email in the JWT claim `email`; users can edit their `user_metadata`. Times are compared with `now()`.

R1. Members can see their organizations and every member of those organizations.
R2. Only admins of an organization can see, create and delete its invites. An invite they create names themselves as `invited_by`, is not yet accepted and expires in the future. Nobody else can read invites, so knowing a token is the only way to use one.
R3. `accept_invite` adds the caller to the invite's organization with the invite's role and marks the invite accepted. It must raise an error and change nothing when the caller is not signed in, the token is unknown, the invite has expired or was already accepted, or the invite's email differs from the caller's verified email (ignoring upper and lower case; `user_metadata` never counts).
R4. Apart from `accept_invite`, nobody can add or change memberships or organizations through the app.
R5. Anonymous visitors cannot see or change anything.
R6. Server-side code using the service role keeps full access.

RLSBENCH-CANARY-f9002c750838f00b
