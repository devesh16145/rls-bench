A hospital records system built with supabase-js. Clinicians normally see only their care-team patients. In an emergency a clinician can "break the glass" with `supabase.rpc('break_glass', { p_patient_id, p_reason })`, implemented as `public.break_glass(p_patient_id bigint, p_reason text) returns timestamptz`, which grants access to that patient for one hour and returns when it expires. Times are compared with `now()`.

R1. Clinicians can read the medical records of patients in their care team, and of patients for whom they hold an unexpired break-glass grant.
R2. `break_glass` creates a grant for the calling clinician that expires one hour later, and returns the expiry time.
R3. `break_glass` must raise an error and change nothing when the caller is not a clinician, the patient does not exist, or the reason (ignoring surrounding spaces) is shorter than 10 characters.
R4. Nobody can create, change or delete grants or records directly through the app. Clinicians can see their own grants; auditors can see every grant.
R5. Anonymous visitors cannot see or change anything.
R6. Server-side code using the service role keeps full access.

RLSBENCH-CANARY-f9002c750838f00b
