A warehouse app built with supabase-js. Staff move stock with `supabase.rpc('transfer_stock', { p_from, p_to, p_sku, p_qty })`, implemented as `public.transfer_stock(p_from bigint, p_to bigint, p_sku text, p_qty integer) returns integer`, which returns the quantity left at the source.

R1. Signed-in users can see the list of warehouses. Staff can see the stock of their warehouses and every transfer into or out of them.
R2. Nobody can change stock or transfers directly through the app.
R3. `transfer_stock` moves `p_qty` units of `p_sku` from `p_from` to `p_to` (creating the destination's stock row if needed) and records a transfer by the caller.
R4. `transfer_stock` must raise an error and change nothing when the caller is not staff of the source warehouse, the quantity is not positive, the source does not have enough stock, or the destination is the source itself or does not exist.
R5. Anonymous visitors cannot see or change anything.
R6. Server-side code using the service role keeps full access.

RLSBENCH-CANARY-f9002c750838f00b
