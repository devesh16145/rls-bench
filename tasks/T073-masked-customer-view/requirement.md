A support console built with supabase-js. Support agents (listed in `support_agents` with their region) look customers up with `supabase.from('support_customers').select()`; supervisors (listed in `supervisors`) use the full `customers` table. Users can edit their own `user_metadata`.

R1. Supervisors can read the full `customers` table. Nobody else can read it, including support agents.
R2. Provide a view `public.support_customers` with exactly the columns `id`, `region`, `full_name`, `email_masked` and `phone_masked`. `email_masked` is the email's first character, then `***`, then everything from the `@` on (asha@example.com becomes a***@example.com). `phone_masked` is `******` followed by the phone's last four digits.
R3. A support agent sees in `support_customers` only the customers of their own region, as recorded in `support_agents`; nothing in `user_metadata` changes their region. Other signed-in users see no rows in it.
R4. Users can see their own `support_agents` and `supervisors` rows. Nobody can change customers, agents or supervisors through the app.
R5. Anonymous visitors cannot see anything.
R6. Server-side code using the service role keeps full access and sees every customer in `support_customers`.

RLSBENCH-CANARY-f9002c750838f00b
