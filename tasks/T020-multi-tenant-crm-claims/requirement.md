A multi-tenant CRM built with supabase-js. The server puts each user's tenant and tenant role into the JWT as `app_metadata.tenant_id` and `app_metadata.tenant_role` (`admin` or `agent`); users cannot edit `app_metadata`, but they can edit `user_metadata`. Writes read the row back with `.select()`.

R1. A user's tenant and tenant role come only from `app_metadata.tenant_id` and `app_metadata.tenant_role`. Nothing in `user_metadata` counts, and users without a tenant claim get no access to tenant data.
R2. Users can read the contacts of their own tenant, except archived contacts, which only their tenant's admins can read. Users never see another tenant's data.
R3. Users can create contacts in their own tenant, as the owner and not archived. Contact owners and tenant admins can edit their tenant's contacts; a contact can never be moved to another tenant.
R4. Only tenant admins can archive contacts or delete them.
R5. Users can read their own tenant's settings row. Only that tenant's admins can change it, and nobody can create or delete settings rows through the app.
R6. Anonymous visitors cannot see or change anything.
R7. Server-side code using the service role keeps full access.

RLSBENCH-CANARY-f9002c750838f00b
