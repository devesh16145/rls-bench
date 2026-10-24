A pharmacy app built with supabase-js. Prescriptions are entered by a server integration using the service role. Pharmacists dispense with `supabase.rpc('dispense', { p_prescription_id })`. Implement it as `public.dispense(p_prescription_id bigint) returns integer`, returning the refills left afterwards. Expiry is compared with `now()`.

R1. Signed-in users can see who the pharmacists are. Patients can see their own prescriptions and the dispenses of them; pharmacists can see every prescription and every dispense.
R2. Nobody can create, change or delete prescriptions or dispenses directly through the app.
R3. `dispense` takes one refill off the prescription and records a dispense by the calling pharmacist.
R4. `dispense` must raise an error and change nothing when the caller is not a pharmacist, the prescription does not exist, has expired or has no refills left, or the prescription is the caller's own.
R5. Anonymous visitors cannot see or change anything.
R6. Server-side code using the service role keeps full access.

RLSBENCH-CANARY-f9002c750838f00b
