A public website's contact form, built with supabase-js. The form submits with `supabase.from('contact_messages').insert({ name, email, body })` and does not read the row back. Staff handle messages in an internal tool that runs on the server with the service role.

R1. Anyone, including anonymous visitors and signed-in users, can submit a message.
R2. A submitted message always starts with status `new` and no `handled_by`; submitters cannot set either.
R3. Nobody can read, change or delete messages through the app, including the person who sent them.
R4. Server-side code using the service role keeps full access.

RLSBENCH-CANARY-f9002c750838f00b
