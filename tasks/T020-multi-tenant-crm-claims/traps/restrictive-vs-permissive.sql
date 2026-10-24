create schema private;

grant usage on schema private to authenticated;

create function private.tenant_id() returns text
language sql stable
as $$
  select auth.jwt() -> 'app_metadata' ->> 'tenant_id'
$$;

create function private.is_tenant_admin() returns boolean
language sql stable
as $$
  select coalesce(auth.jwt() -> 'app_metadata' ->> 'tenant_role' = 'admin', false)
$$;

alter table public.contacts enable row level security;
alter table public.tenant_settings enable row level security;

create policy contacts_tenant_isolation on public.contacts
  for all to authenticated
  using (tenant_id = private.tenant_id())
  with check (tenant_id = private.tenant_id());

create policy contacts_select on public.contacts
  for select to authenticated
  using (not is_archived or private.is_tenant_admin());

create policy contacts_insert on public.contacts
  for insert to authenticated
  with check (owner_id = auth.uid() and not is_archived);

create policy contacts_update on public.contacts
  for update to authenticated
  using (owner_id = auth.uid() or private.is_tenant_admin())
  with check (
    (owner_id = auth.uid() or private.is_tenant_admin())
    and (not is_archived or private.is_tenant_admin())
  );

create policy contacts_delete on public.contacts
  for delete to authenticated
  using (private.is_tenant_admin());

create policy tenant_settings_select on public.tenant_settings
  for select to authenticated
  using (tenant_id = private.tenant_id());

create policy tenant_settings_update on public.tenant_settings
  for update to authenticated
  using (tenant_id = private.tenant_id() and private.is_tenant_admin())
  with check (tenant_id = private.tenant_id() and private.is_tenant_admin());
