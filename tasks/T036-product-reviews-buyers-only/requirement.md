A shop built with supabase-js. Purchases are recorded by the server. Customers write or update their review with `supabase.from('reviews').upsert({ product_id, user_id, rating, body }).select()`. Staff choose featured reviews in an admin tool that uses the service role.

R1. Anyone, including anonymous visitors, can read products and reviews.
R2. Users can see only their own purchases. Nobody can record purchases through the app.
R3. Signed-in users can write one review per product, as themselves, only for products they have purchased, and can edit and delete their own reviews.
R4. Only staff decide which reviews are featured: users can never set or change `is_featured`, even on their own reviews.
R5. Anonymous visitors cannot write anything.
R6. Server-side code using the service role keeps full access.

RLSBENCH-CANARY-f9002c750838f00b
