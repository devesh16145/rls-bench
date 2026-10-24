A developer dashboard built with supabase-js. Server code records daily API usage. The dashboard shows a chart with `supabase.from('api_usage').select()` and totals with `supabase.from('usage_summary').select()`.

R1. Users can read only their own daily usage rows.
R2. Provide a view `public.usage_summary` with exactly the columns `user_id`, `total_requests` (sum of requests) and `active_days` (number of days with usage), one row per user. Signed-in users see only their own row in it.
R3. Nobody can change usage through the app.
R4. Anonymous visitors cannot see anything, including `usage_summary`.
R5. Server-side code using the service role keeps full access and sees every user in `usage_summary`.

RLSBENCH-CANARY-f9002c750838f00b
