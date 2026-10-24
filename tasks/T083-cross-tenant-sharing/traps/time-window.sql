create schema private;

grant usage on schema private to authenticated;

create function private.tenant() returns text
language sql stable
as $$
  select auth.jwt() -> 'app_metadata' ->> 'tenant_id'
$$;

create function private.is_admin() returns boolean
language sql stable
as $$
  select coalesce(auth.jwt() -> 'app_metadata' ->> 'role' = 'admin', false)
$$;

create function private.item_tenant(p_item_id bigint) returns text
language sql stable security definer set search_path = ''
as $$
  select i.tenant_id from public.items i where i.id = p_item_id
$$;

alter table public.items enable row level security;
alter table public.item_shares enable row level security;

create policy items_select on public.items
  for select to authenticated
  using (
    tenant_id = private.tenant()
    or exists (
      select 1 from public.item_shares s
      where s.item_id = items.id and s.target_tenant = private.tenant()
    )
  );

create policy items_insert on public.items
  for insert to authenticated
  with check (tenant_id = private.tenant() and private.is_admin());

create policy items_update on public.items
  for update to authenticated
  using (tenant_id = private.tenant() and private.is_admin())
  with check (tenant_id = private.tenant() and private.is_admin());

create policy items_delete on public.items
  for delete to authenticated
  using (tenant_id = private.tenant() and private.is_admin());

create policy shares_select on public.item_shares
  for select to authenticated
  using (private.item_tenant(item_id) = private.tenant() or target_tenant = private.tenant());

create policy shares_insert on public.item_shares
  for insert to authenticated
  with check (private.item_tenant(item_id) = private.tenant() and private.is_admin());

create policy shares_update on public.item_shares
  for update to authenticated
  using (private.item_tenant(item_id) = private.tenant() and private.is_admin())
  with check (private.item_tenant(item_id) = private.tenant() and private.is_admin());

create policy shares_delete on public.item_shares
  for delete to authenticated
  using (private.item_tenant(item_id) = private.tenant() and private.is_admin());
