A telehealth app built with supabase-js. Doctors must use multi-factor authentication: Supabase sets the JWT claim `aal` to `aal2` in a session that passed an MFA challenge and to `aal1` otherwise. Doctors add notes with `supabase.from('records').insert({ patient_id, author_id, note }).select()`.

R1. Patients can read their own patient row and their own records, whatever the session's assurance level.
R2. Doctors can read the patient rows and records of patients whose care team they are in, but only in sessions with `aal2`.
R3. Doctors can add records, as the author, for patients whose care team they are in, only in sessions with `aal2`. Patients cannot add records.
R4. Records can never be changed or deleted through the app.
R5. Users can see the care-team rows that involve them, as the patient or as the doctor. Nobody can change care teams through the app.
R6. Access comes only from the patient and care-team tables; nothing in a user's metadata grants it.
R7. Anonymous visitors cannot see or change anything.
R8. Server-side code using the service role keeps full access.

RLSBENCH-CANARY-f9002c750838f00b
