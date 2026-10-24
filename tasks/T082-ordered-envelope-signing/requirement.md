An e-signature app built with supabase-js. Envelopes and their recipients are created by a server API using the service role; recipients must sign in `sign_order`. Recipients sign with `supabase.rpc('sign_envelope', { p_envelope_id })` and senders cancel with `supabase.rpc('void_envelope', { p_envelope_id })`. Implement them as `public.sign_envelope(p_envelope_id bigint) returns text` and `public.void_envelope(p_envelope_id bigint) returns text`, each returning the envelope's status afterwards.

R1. Senders and recipients can see their envelopes and the full recipient list of those envelopes.
R2. Nobody can create, change or delete envelopes or recipient rows directly through the app.
R3. `sign_envelope` records the caller's signature. Once every recipient has signed, the envelope becomes `completed`. It must raise an error and change nothing when the caller is not a recipient, has already signed, the envelope is not `sent`, or a recipient earlier in `sign_order` has not signed yet.
R4. `void_envelope` lets the sender cancel an envelope that is still `sent`. It must raise an error and change nothing for anyone else or for envelopes that are not `sent`.
R5. Anonymous visitors cannot see or change anything.
R6. Server-side code using the service role keeps full access.

RLSBENCH-CANARY-f9002c750838f00b
