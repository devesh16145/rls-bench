A B2B portal built with supabase-js. The server puts each user's tenant and role in the JWT as `app_metadata.tenant_id` and `app_metadata.role` (`admin` or `member`); users can edit their `user_metadata`. A tenant can share an item with another tenant through `item_shares`, optionally until `expires_at` (compared with `now()`). Writes read the row back with `.select()`.

R1. Users can see their own tenant's items, plus items shared with their tenant whose share has not expired.
R2. Only admins of a tenant can create, edit and delete that tenant's items. Tenants an item is shared with can read it but never change it.
R3. Only admins of the tenant that owns an item can create, change and remove its shares, so recipients can never pass an item on to another tenant.
R4. Users can see the shares of their own tenant's items and the shares addressed to their tenant.
R5. Tenant and role come only from `app_metadata`; nothing in `user_metadata` counts. Anonymous visitors cannot see or change anything.
R6. Server-side code using the service role keeps full access.

RLSBENCH-CANARY-f9002c750838f00b
