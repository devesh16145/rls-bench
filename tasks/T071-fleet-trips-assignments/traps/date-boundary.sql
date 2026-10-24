create schema private;

grant usage on schema private to authenticated;

create function private.is_manager() returns boolean
language sql stable security definer set search_path = ''
as $$
  select exists (select 1 from public.fleet_managers m where m.user_id = auth.uid())
$$;

create function private.covered(p_vehicle_id bigint, p_day date) returns boolean
language sql stable security definer set search_path = ''
as $$
  select exists (select 1 from public.assignments a where a.vehicle_id = p_vehicle_id and a.driver_id = auth.uid() and p_day >= a.starts_on and p_day < a.ends_on)
$$;

alter table public.fleet_managers enable row level security;
alter table public.vehicles enable row level security;
alter table public.assignments enable row level security;
alter table public.trips enable row level security;

create policy vehicles_select on public.vehicles
  for select to authenticated
  using (true);

create policy assignments_select on public.assignments
  for select to authenticated
  using (driver_id = auth.uid() or private.is_manager());

create policy assignments_insert on public.assignments
  for insert to authenticated
  with check (private.is_manager());

create policy assignments_update on public.assignments
  for update to authenticated
  using (private.is_manager())
  with check (private.is_manager());

create policy assignments_delete on public.assignments
  for delete to authenticated
  using (private.is_manager());

create policy trips_select on public.trips
  for select to authenticated
  using (driver_id = auth.uid() or private.is_manager());

create policy trips_insert on public.trips
  for insert to authenticated
  with check (driver_id = auth.uid() and private.covered(vehicle_id, trip_date));

create policy trips_update on public.trips
  for update to authenticated
  using (driver_id = auth.uid())
  with check (driver_id = auth.uid() and private.covered(vehicle_id, trip_date));

create policy trips_delete on public.trips
  for delete to authenticated
  using (driver_id = auth.uid());
