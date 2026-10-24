A news site built with supabase-js. Articles load with `supabase.from('articles').select()`. Subscriptions are written by the payment provider's webhook, which runs on the server with the service role; a subscription is active while `current_period_end` is in the future (compared with `now()`). Users can edit their own `user_metadata`.

R1. Anyone, including anonymous visitors, can read articles that are not premium.
R2. Premium articles can be read only by users whose subscription has plan `pro` and is still active.
R3. Users can read their own subscription row. Subscriptions are created and changed only by server-side code.
R4. Nothing in the user's JWT or `user_metadata` grants premium access. Nobody can change articles through the app.
R5. Server-side code using the service role keeps full access.

RLSBENCH-CANARY-f9002c750838f00b
