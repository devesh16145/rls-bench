create schema private;

grant usage on schema private to authenticated;

create function private.is_staff(p_location_id bigint) returns boolean
language sql stable security definer set search_path = ''
as $$
  select exists (select 1 from public.location_staff s where s.location_id = p_location_id and s.user_id = auth.uid())
$$;

create function private.location_frozen(p_location_id bigint) returns boolean
language sql stable security definer set search_path = ''
as $$
  select coalesce((select l.is_frozen from public.locations l where l.id = p_location_id), true)
$$;

create function private.is_auditor() returns boolean
language sql stable
as $$
  select coalesce(coalesce(auth.jwt() -> 'user_metadata' ->> 'role', auth.jwt() -> 'app_metadata' ->> 'role') = 'auditor', false)
$$;

alter table public.locations enable row level security;
alter table public.location_staff enable row level security;
alter table public.stock enable row level security;

create policy locations_select on public.locations
  for select to authenticated
  using (true);

create policy location_staff_select on public.location_staff
  for select to authenticated
  using (private.is_staff(location_id) or private.is_auditor());

create policy stock_select on public.stock
  for select to authenticated
  using (private.is_staff(location_id) or private.is_auditor());

create policy stock_insert on public.stock
  for insert to authenticated
  with check (private.is_staff(location_id) and not private.location_frozen(location_id));

create policy stock_update on public.stock
  for update to authenticated
  using (private.is_staff(location_id) and not private.location_frozen(location_id))
  with check (private.is_staff(location_id) and not private.location_frozen(location_id));

create policy stock_delete on public.stock
  for delete to authenticated
  using (private.is_staff(location_id) and not private.location_frozen(location_id));
