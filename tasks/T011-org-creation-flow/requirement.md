A team app built with supabase-js. Users create organizations and manage who belongs to them. To create an organization the app calls `supabase.from('orgs').insert({ name }).select()` (so the new row is read back immediately), then inserts the creator's membership with role `owner`. Other writes also use `.select()` to read back the written row.

R1. Any signed-in user can create an organization; its `created_by` is always themselves.
R2. The creator of an organization that has no members yet can add themselves to it as `owner`. Apart from this, nobody can add themselves to an organization.
R3. Members can see the organizations they belong to and every membership row of those organizations. The creator of an organization can also see it before joining it.
R4. Owners and admins can add people with role `member` and remove memberships whose role is `member`. Only owners can give someone the role `admin` or `owner`, change someone's role, or remove admins and owners.
R5. Any member can leave an organization by deleting their own membership, except an organization's only owner.
R6. Nobody can change their own role.
R7. Only owners can rename their organization. Organizations cannot be deleted through the app.
R8. Anonymous visitors cannot see or change anything.
R9. Server-side code using the service role keeps full access.

RLSBENCH-CANARY-f9002c750838f00b
