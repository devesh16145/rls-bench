An inventory app built with supabase-js. Staff set stock levels with `supabase.from('stock').upsert({ location_id, sku, qty }).select()` and remove items with `.delete()`. The server marks auditors with `app_metadata.role = 'auditor'` in their JWT; users can edit their own `user_metadata`. During a stock count a location is frozen.

R1. Signed-in users can see the list of locations. Staff can see the stock and staff list of their own locations. Auditors can see all stock and all staff lists.
R2. Staff can add, change and remove stock rows at their own locations only, and stock can never be moved to a location where they are not staff.
R3. While a location is frozen, nobody can add, change or remove its stock through the app.
R4. Auditors can never change stock. Auditor status comes only from `app_metadata.role`; `user_metadata` never counts.
R5. Nobody can change locations or staff lists through the app.
R6. Anonymous visitors cannot see or change anything.
R7. Server-side code using the service role keeps full access.

RLSBENCH-CANARY-f9002c750838f00b
