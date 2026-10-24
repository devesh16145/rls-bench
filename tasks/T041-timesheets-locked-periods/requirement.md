A timesheet app built with supabase-js. Employees log time with `supabase.from('time_entries').insert({...}).select()` and edit entries with `.update({...}).eq('id', id).select()`. Finance locks a pay period once payroll has run. A nightly payroll import runs on the server with the service role and may need to correct entries in any period, locked or not.

R1. Users can see their own time entries, the projects they are assigned to, their own assignments and every pay period.
R2. Users can log, edit and delete their own entries, only for projects they are assigned to.
R3. Entries in a locked period cannot be created, changed or deleted through the app, and an entry cannot be moved into or out of a locked period.
R4. Nobody can change projects, assignments or periods through the app.
R5. Anonymous visitors cannot see or change anything.
R6. The payroll import, running with the service role, can create and change any entry, including in locked periods.

RLSBENCH-CANARY-f9002c750838f00b
