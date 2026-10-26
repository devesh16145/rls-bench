A home-camera app built with supabase-js. Owners share a camera with `supabase.from('camera_shares').insert({ camera_id, grantee_id, expires_at, created_by }).select()`. Watching a stream needs the camera's row in `stream_keys`, which the app reads only after the user has completed multi-factor authentication; the session's assurance level is the JWT claim `aal` (`aal2` after MFA). Keys are written by server-side code.

R1. Owners can see their cameras. A user a camera is shared with can see it while the share has not expired (a share with no expiry never expires).
R2. A camera's stream key can be read only by its owner or a user with a current share, and only in a session that completed MFA (`aal2`). In other sessions the key is not readable, even by the owner.
R3. Owners can share their own cameras, as themselves, and remove shares of their cameras. Users a camera is shared with cannot share it on. Shares are never edited; users can see the shares addressed to them and owners the shares of their cameras.
R4. Signed-in users can add cameras as themselves and rename their own cameras. Nobody else changes a camera, and nobody writes stream keys through the app.
R5. Anonymous visitors cannot see or change anything. Server-side code using the service role keeps full access.

RLSBENCH-CANARY-f9002c750838f00b
