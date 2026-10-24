A B2B workspace built with supabase-js. Supabase puts the session's sign-in methods in the JWT claim `amr`, an array of objects like `{ "method": "password", "timestamp": 1700000000 }`; a single sign-on session contains an entry with method `sso/saml`. Users can edit their `user_metadata`. Writes read the row back with `.select()`.

R1. Members can see their organizations, the members of those organizations and their documents. For an organization with `require_sso`, all of this is visible only in sessions whose `amr` contains the method `sso/saml`.
R2. Organization admins can create, edit and delete their organization's documents, under the same session requirement.
R3. Organization admins can change their organization's settings, under the same session requirement.
R4. Only the `amr` claim counts as proof of an SSO session; nothing in `user_metadata` does. Nobody can change memberships through the app.
R5. Anonymous visitors cannot see or change anything.
R6. Server-side code using the service role keeps full access.

RLSBENCH-CANARY-f9002c750838f00b
