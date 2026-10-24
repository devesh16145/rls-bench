An auction site built with supabase-js. Bidders call `supabase.rpc('place_bid', { p_auction_id, p_amount })`. Implement it as `public.place_bid(p_auction_id bigint, p_amount numeric) returns numeric`, returning the new highest bid. Auction end times are compared with `now()`.

R1. Signed-in users can see every auction, including its current highest bid. Bidders can see their own bids; sellers can see every bid on their auctions.
R2. Nobody can create, change or delete auctions or bids directly through the app.
R3. `place_bid` records a bid by the caller and makes it the auction's highest bid.
R4. `place_bid` must raise an error and change nothing when the caller is not signed in, the auction does not exist or has ended, the caller is the seller, or the amount is too low: below the starting price when there are no bids yet, otherwise below the highest bid plus the minimum increment.
R5. Anonymous visitors cannot see or change anything.
R6. Server-side code using the service role keeps full access.

RLSBENCH-CANARY-f9002c750838f00b
