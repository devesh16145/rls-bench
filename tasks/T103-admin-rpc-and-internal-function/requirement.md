A team app built with supabase-js. Admins change roles with `supabase.rpc('set_member_role', { p_org_id, p_user_id, p_role })`, implemented as `public.set_member_role(p_org_id bigint, p_user_id uuid, p_role text) returns text` (returning the new role). A nightly server job calls `public.recalculate_leaderboard() returns void`, which you also write; in Supabase, functions in `public` can be called through the API by anyone who has `EXECUTE` on them.

R1. Members can see their organization's memberships. Signed-in users can see the leaderboard.
R2. Nobody can change memberships or the leaderboard directly through the app.
R3. `set_member_role` lets an owner or admin of the organization set another member's role to `admin` or `member`. It must raise an error and change nothing when the caller is not an owner or admin there, targets themselves, targets an owner, targets someone outside the organization, or asks for any other role.
R4. `recalculate_leaderboard` is internal: anonymous visitors and signed-in users must not be able to execute it at all. Only the service role can.
R5. Anonymous visitors cannot see or change anything.
R6. Server-side code using the service role keeps full access.

RLSBENCH-CANARY-f9002c750838f00b
