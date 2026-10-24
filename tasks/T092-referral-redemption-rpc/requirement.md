A fintech app built with supabase-js. Each user has a referral code created by the server. A new user enters a friend's code with `supabase.rpc('redeem_referral', { p_code })`. Implement it as `public.redeem_referral(p_code text) returns bigint`, returning the new referral's id. Each successful redemption gives 100 credits to the new user and 100 to the code's owner.

R1. Users can see their own referral code, the referrals they made or received, and their own credits.
R2. Nobody can create, change or delete referral codes, referrals or credits directly through the app.
R3. `redeem_referral` records a referral from the code's owner to the caller and gives each of them 100 credits.
R4. `redeem_referral` must raise an error and change nothing when the caller is not signed in, the code does not exist, the code is the caller's own, the caller has already redeemed a referral code, or the code's owner already has 5 referrals.
R5. Anonymous visitors cannot see or change anything.
R6. Server-side code using the service role keeps full access.

RLSBENCH-CANARY-f9002c750838f00b
