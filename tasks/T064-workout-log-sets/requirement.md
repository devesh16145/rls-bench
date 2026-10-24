A fitness app built with supabase-js. Users log a workout with `supabase.from('workouts').insert({...}).select()` and its sets with `supabase.from('workout_sets').insert({...}).select()`; edits use `.update({...}).eq('id', id).select()`.

R1. Users can read, create, edit and delete only their own workouts.
R2. A workout's sets can be read, added, edited and deleted only by the workout's owner, and a set can never be moved to someone else's workout.
R3. Anonymous visitors cannot see or change anything.
R4. Server-side code using the service role keeps full access.

RLSBENCH-CANARY-f9002c750838f00b
