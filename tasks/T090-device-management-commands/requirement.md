A device-management console built with supabase-js. Commands are queued with `supabase.from('device_commands').insert({ device_id, command, issued_by }).select()`; an agent on the device runs them. `org_admins` lists each organization's IT admins.

R1. Employees can see the devices assigned to them and those devices' commands. IT admins can see every device and command of their organization.
R2. IT admins can issue any command (`locate`, `lock` or `wipe`) to devices of their organization, as themselves.
R3. Employees can issue only `locate` and `lock`, as themselves, and only to devices assigned to them. They can never issue `wipe`.
R4. Commands can never be changed or deleted, and nobody can change devices or `org_admins` through the app.
R5. Anonymous visitors cannot see or change anything.
R6. Server-side code using the service role keeps full access.

RLSBENCH-CANARY-f9002c750838f00b
