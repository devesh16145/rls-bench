A social app built with supabase-js. Friend requests are sent with `supabase.from('friendships').insert({ requester_id, addressee_id }).select()` and accepted with `.update({ status: 'accepted' }).match({ requester_id, addressee_id })`. Two users are friends when a friendship between them, in either direction, is `accepted`.

R1. Signed-in users can read public posts, posts with audience `friends` by people they are friends with, and all of their own posts. Anonymous visitors can read public posts only.
R2. Users can write, edit and delete only their own posts, and a post can never be given to another author.
R3. Users can send friend requests as the requester, and new requests are always pending.
R4. Only the addressee of a pending request can accept it. Requesters cannot accept their own requests, and nothing else about a friendship can be changed.
R5. Either person can delete a friendship or request (unfriend, cancel or decline). Users can see the friendships and requests they are part of.
R6. Server-side code using the service role keeps full access.

RLSBENCH-CANARY-f9002c750838f00b
