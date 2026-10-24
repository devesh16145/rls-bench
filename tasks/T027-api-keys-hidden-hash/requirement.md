A developer dashboard built with supabase-js. API keys are created by a server function using the service role, which stores only a hash of each key. The dashboard lists keys with `supabase.from('api_keys').select('id, name, last4, created_at, revoked_at')` and revokes a key with `supabase.from('api_keys').update({ revoked_at }).eq('id', id)` without reading it back.

R1. Users can list their own keys: `id`, `name`, `last4`, `created_at` and `revoked_at`. Nobody can read `key_hash` through the app, not even for their own keys.
R2. Users can revoke their own active keys by setting `revoked_at`. Nothing else about a key can change, and a revoked key can no longer be changed.
R3. Users cannot create or delete keys through the app.
R4. Anonymous visitors cannot see or change any keys.
R5. Server-side code using the service role keeps full access, including `key_hash`.

RLSBENCH-CANARY-f9002c750838f00b
