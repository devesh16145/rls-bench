An escrow marketplace built with supabase-js. Buyers place orders with `supabase.from('orders').insert({ listing_id, buyer_id, seller_id, amount }).select()`. The payment provider's webhook (server, service role) moves an order from `pending_payment` to `paid`. After that the app calls `supabase.rpc('mark_shipped' | 'release_funds' | 'refund_order', { p_order_id })`. Implement these as `public.mark_shipped(p_order_id bigint) returns text`, `public.release_funds(p_order_id bigint) returns text` and `public.refund_order(p_order_id bigint) returns text`, each returning the new status.

R1. Signed-in users can see every listing. Buyers and sellers can see the orders they are part of.
R2. Buyers can place orders as themselves; the order's `seller_id` and `amount` must match the listing's seller and price, new orders are always `pending_payment`, and nobody can buy their own listing.
R3. Nobody can change or delete orders directly through the app; status changes go only through the three functions (and server-side code).
R4. `mark_shipped` lets the order's seller move it from `paid` to `shipped`. `release_funds` lets the order's buyer move it from `shipped` to `released`. `refund_order` lets the order's seller move it from `paid` or `shipped` to `refunded`.
R5. Each function must raise an error and change nothing when the order does not exist, the caller is not the party named above, or the order is not in an allowed status.
R6. Anonymous visitors cannot see or change anything.
R7. Server-side code using the service role keeps full access.

RLSBENCH-CANARY-f9002c750838f00b
