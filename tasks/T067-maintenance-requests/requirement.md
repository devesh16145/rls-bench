A building-management app built with supabase-js. Residents report problems with `supabase.from('requests').insert({ unit_id, created_by, description }).select()` and attach photos with `.from('request_photos').insert({ request_id, path }).select()`. Building staff update progress with `.update({ status }).eq('id', id).select()`.

R1. Residents can see their own units and the requests and photos of their own units. Building staff can see the units, requests and photos of every unit in their buildings.
R2. Residents can create requests for their own units, as themselves; new requests are always `open`.
R3. Residents and staff can add photos to the requests they can see.
R4. Building staff can change the status of requests in their buildings. Nobody can change anything else about a request, residents cannot change status, and requests are never deleted.
R5. Users can see their own residence and staff rows. Nobody can change units, residents or staff through the app.
R6. Anonymous visitors cannot see or change anything.
R7. Server-side code using the service role keeps full access.

RLSBENCH-CANARY-f9002c750838f00b
