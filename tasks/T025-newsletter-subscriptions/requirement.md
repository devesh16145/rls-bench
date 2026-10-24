A newsletter built with supabase-js. Visitors subscribe with `supabase.from('subscriptions').insert({ email, topic })` and do not read the row back. Confirmation links are handled by server code using the service role. Signed-in users manage the subscriptions of their own address on a settings page; Supabase puts the account's verified email address in the JWT claim `email`. Users can edit their `user_metadata`.

R1. Anyone, including anonymous visitors, can subscribe an email address. New subscriptions are always unconfirmed.
R2. Signed-in users can see and delete the subscriptions whose email matches the `email` claim in their JWT, ignoring upper and lower case.
R3. Nobody can confirm a subscription or change its email or topic through the app.
R4. An email address in `user_metadata` never counts.
R5. Anonymous visitors cannot read or delete subscriptions.
R6. Server-side code using the service role keeps full access.

RLSBENCH-CANARY-f9002c750838f00b
