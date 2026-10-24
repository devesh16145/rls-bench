A mobile app built with supabase-js registers its push-notification token on every launch with `supabase.from('push_tokens').upsert({ token, user_id, platform }, { onConflict: 'token' }).select()`. Knowing a token is enough to send notifications to that device.

R1. Users can see only their own tokens.
R2. Users can register tokens for themselves and refresh their own tokens. A token registered to another user can never be taken over or reassigned.
R3. Users can delete their own tokens.
R4. Anonymous visitors cannot see or change any tokens.
R5. Server-side code using the service role keeps full access.

RLSBENCH-CANARY-f9002c750838f00b
