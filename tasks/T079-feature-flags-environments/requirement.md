A feature-flag service built with supabase-js. Each organization has flags in two environments, `dev` and `prod`. Flags are created with `supabase.from('flags').insert({...}).select()` and toggled with `.update({...}).eq('id', id).select()`.

R1. Members can see their organization, its members and all of its flags in both environments.
R2. Developers and admins can create, change and delete their organization's `dev` flags.
R3. Only admins can create, change or delete `prod` flags, and developers can never move a flag into `prod`.
R4. Nobody can change organizations or memberships through the app.
R5. Anonymous visitors cannot see or change anything.
R6. Server-side code using the service role keeps full access.

RLSBENCH-CANARY-f9002c750838f00b
