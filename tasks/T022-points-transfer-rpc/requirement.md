A rewards app built with supabase-js. Users send points to each other by calling the RPC `supabase.rpc('send_points', { p_to, p_amount })`. Implement it as `public.send_points(p_to uuid, p_amount integer) returns bigint`, returning the new transfer's id.

R1. Users can read only their own wallet.
R2. Users can read the transfers they sent or received.
R3. Nobody can create, change or delete wallets or transfers directly through the app.
R4. `send_points` moves `p_amount` points from the caller's wallet to the wallet of `p_to` and records a transfer from the caller. It must raise an error and change nothing when the caller is not signed in, the amount is not positive, the caller does not have enough points, the recipient has no wallet, or the recipient is the caller.
R5. Server-side code using the service role keeps full access to the tables.

RLSBENCH-CANARY-f9002c750838f00b
