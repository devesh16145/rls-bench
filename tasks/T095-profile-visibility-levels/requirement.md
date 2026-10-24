A professional network built with supabase-js. Each user has at most one profile and chooses who can see it: `public` (anyone, including logged-out visitors), `members` (any signed-in user) or `private` (only themselves). Profiles are saved with `.insert({...}).select()` and `.update({...}).eq('user_id', id).select()`.

R1. Anyone, including anonymous visitors, can read public profiles.
R2. Signed-in users can also read members-only profiles. Private profiles are visible only to their owner.
R3. Users can create, edit and delete only their own profile, and a profile can never be moved to another user.
R4. Anonymous visitors cannot create or change profiles.
R5. Server-side code using the service role keeps full access.

RLSBENCH-CANARY-f9002c750838f00b
