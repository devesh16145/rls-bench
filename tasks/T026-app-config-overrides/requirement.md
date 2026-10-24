A web app built with supabase-js. On startup it loads configuration with `supabase.from('app_config').select()`. A user's personal preferences are saved with `supabase.from('user_flag_overrides').upsert({ user_id, key, value }).select()`.

R1. Anyone, including anonymous visitors, can read public config entries. Entries that are not public are visible only to server-side code.
R2. Nobody can change `app_config` through the app.
R3. Signed-in users can read only their own overrides.
R4. Signed-in users can create, change and delete their own overrides, only for config keys that are public and marked `user_overridable`.
R5. Anonymous visitors cannot read or change overrides.
R6. Server-side code using the service role keeps full access.

RLSBENCH-CANARY-f9002c750838f00b
