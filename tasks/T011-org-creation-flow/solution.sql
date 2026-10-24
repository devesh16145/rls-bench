create schema private;

grant usage on schema private to authenticated;

create function private.org_role(p_org_id bigint) returns text
language sql stable security definer set search_path = ''
as $$
  select m.role from public.org_members m
  where m.org_id = p_org_id and m.user_id = auth.uid()
$$;

create function private.can_bootstrap(p_org_id bigint) returns boolean
language sql stable security definer set search_path = ''
as $$
  select exists (select 1 from public.orgs o where o.id = p_org_id and o.created_by = auth.uid())
    and not exists (select 1 from public.org_members m where m.org_id = p_org_id)
$$;

create function private.has_other_owner(p_org_id bigint) returns boolean
language sql stable security definer set search_path = ''
as $$
  select exists (
    select 1 from public.org_members m
    where m.org_id = p_org_id and m.role = 'owner' and m.user_id <> auth.uid()
  )
$$;

alter table public.orgs enable row level security;
alter table public.org_members enable row level security;

create policy orgs_select on public.orgs
  for select to authenticated
  using (created_by = auth.uid() or private.org_role(id) is not null);

create policy orgs_insert on public.orgs
  for insert to authenticated
  with check (created_by = auth.uid());

create policy orgs_update on public.orgs
  for update to authenticated
  using (private.org_role(id) = 'owner')
  with check (private.org_role(id) = 'owner');

create policy org_members_select on public.org_members
  for select to authenticated
  using (user_id = auth.uid() or private.org_role(org_id) is not null);

create policy org_members_insert on public.org_members
  for insert to authenticated
  with check (
    (user_id = auth.uid() and role = 'owner' and private.can_bootstrap(org_id))
    or (user_id <> auth.uid() and role = 'member' and private.org_role(org_id) in ('owner', 'admin'))
    or (user_id <> auth.uid() and private.org_role(org_id) = 'owner')
  );

create policy org_members_update on public.org_members
  for update to authenticated
  using (user_id <> auth.uid() and private.org_role(org_id) = 'owner')
  with check (user_id <> auth.uid() and private.org_role(org_id) = 'owner');

create policy org_members_delete on public.org_members
  for delete to authenticated
  using (
    (user_id = auth.uid() and (role <> 'owner' or private.has_other_owner(org_id)))
    or (user_id <> auth.uid() and role = 'member' and private.org_role(org_id) in ('owner', 'admin'))
    or (user_id <> auth.uid() and private.org_role(org_id) = 'owner')
  );
