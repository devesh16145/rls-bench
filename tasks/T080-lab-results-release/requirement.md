A patient portal built with supabase-js. Doctors add results with `supabase.from('lab_results').insert({...}).select()` and release them to the patient, now or at a later time, with `.update({ released_at }).eq('id', id).select()`. A result is released once `released_at` is set and not in the future (compared with `now()`).

R1. Patients can see their own patient row and care team, and their own lab results once they are released. Doctors in a patient's care team can see that patient and all of the patient's results.
R2. Doctors can add results for patients whose care team they are in.
R3. Doctors in the care team can set or change `released_at` and edit results that are not yet released. Once a result is released, nobody can change it through the app.
R4. Patients cannot add or change results. Nobody can change patients or care teams through the app, and results are never deleted.
R5. Anonymous visitors cannot see or change anything.
R6. Server-side code using the service role keeps full access.

RLSBENCH-CANARY-f9002c750838f00b
