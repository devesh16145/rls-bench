create schema private;

grant usage on schema private to authenticated;

create function private.is_admin() returns boolean
language sql stable security definer set search_path = ''
as $$
  select exists (select 1 from public.org_admins a where a.user_id = auth.uid())
$$;

alter table public.org_admins enable row level security;
alter table public.files enable row level security;

create policy files_select on public.files
  for select to authenticated
  using (owner_id = auth.uid() or private.is_admin());

create policy files_insert on public.files
  for insert to authenticated
  with check (owner_id = auth.uid() and not legal_hold);

create policy files_update on public.files
  for update to authenticated
  using (owner_id = auth.uid() or private.is_admin())
  with check (owner_id = auth.uid() or private.is_admin());

create policy files_delete on public.files
  for delete to authenticated
  using (owner_id = auth.uid() or private.is_admin());

create policy files_hold_blocks_update on public.files
  as restrictive
  for update to authenticated
  using (not legal_hold)
  with check (not legal_hold);
