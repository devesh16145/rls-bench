A compliance-minded records app built with supabase-js. Records are created and edited with `.insert({...}).select()` and `.update({...}).eq('id', id).select()`; admins delete a record by setting `deleted_at`. Admins can undo a deletion with `supabase.rpc('restore_record', { p_record_id })`, implemented as `public.restore_record(p_record_id bigint) returns void`. Time is compared with `now()`.

R1. Members can see their own memberships and their organization's records that are not deleted. Admins can also see deleted records.
R2. Members can create records in their organization and edit its records that are not deleted. Only admins can delete (set `deleted_at`) a record. Records are never hard-deleted.
R3. Every insert and update of a record adds an `audit_log` row with the record's id, the action (`insert` or `update`) and the acting user in `actor`. Nobody can create, change or delete audit rows directly through the app.
R4. Admins can read the audit rows of their organization's records; members cannot read audit rows.
R5. `restore_record` clears `deleted_at`. It must raise an error and change nothing unless the caller is an admin of the record's organization, the record is deleted, and it was deleted within the last 30 days.
R6. Anonymous visitors cannot see or change anything. Server-side code using the service role keeps full access.

RLSBENCH-CANARY-f9002c750838f00b
