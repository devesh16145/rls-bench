A shop built with supabase-js. Product listings are public. The cart page adds an item or changes its quantity with `supabase.from('cart_items').upsert({ user_id, product_id, quantity }).select()` and removes an item with `.delete()`.

R1. Anyone, including anonymous visitors, can read active products. Inactive products are visible only to server-side code.
R2. Nobody can create, change or delete products through the app.
R3. Signed-in users can read only their own cart items.
R4. Signed-in users can add, change and remove items in their own cart only, and only for active products.
R5. Anonymous visitors cannot read or change cart items.
R6. Server-side code using the service role keeps full access.

RLSBENCH-CANARY-f9002c750838f00b
