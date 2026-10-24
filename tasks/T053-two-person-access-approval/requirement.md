An internal tool built with supabase-js for requesting production access. Requests are created with `supabase.from('access_requests').insert({ resource, reason }).select()`. Ops team members approve with `supabase.rpc('approve_access', { p_request_id })`. Implement it as `public.approve_access(p_request_id bigint) returns text`, returning the request's status after the call. A request is granted once two different ops team members have approved it.

R1. Requesters can see their own requests and the approvals on them. Ops team members can see every request and every approval. Signed-in users can see who is on the ops team.
R2. Signed-in users can create requests as themselves; new requests are always `pending`. Requesters can withdraw (delete) their own pending requests.
R3. Nobody can change requests, or create, change or delete approvals, except through `approve_access`.
R4. `approve_access` records an approval by the caller and, once two different ops team members have approved, sets the request to `granted`. It must raise an error and change nothing when the caller is not on the ops team, the request does not exist or is not pending, the caller made the request, or the caller has already approved it.
R5. Anonymous visitors cannot see or change anything.
R6. Server-side code using the service role keeps full access.

RLSBENCH-CANARY-f9002c750838f00b
