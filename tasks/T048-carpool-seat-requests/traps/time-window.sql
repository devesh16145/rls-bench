create schema private;

grant usage on schema private to authenticated;

create function private.is_driver(p_ride_id bigint) returns boolean
language sql stable security definer set search_path = ''
as $$
  select exists (select 1 from public.rides r where r.id = p_ride_id and r.driver_id = auth.uid())
$$;

create function private.ride_upcoming(p_ride_id bigint) returns boolean
language sql stable security definer set search_path = ''
as $$
  select coalesce((select r.departs_at > now() from public.rides r where r.id = p_ride_id), false)
$$;

create function private.seats_left(p_ride_id bigint) returns integer
language sql stable security definer set search_path = ''
as $$
  select r.seats - (select count(*)::integer from public.ride_bookings b where b.ride_id = r.id and b.status = 'confirmed') from public.rides r where r.id = p_ride_id
$$;

alter table public.rides enable row level security;
alter table public.ride_bookings enable row level security;

revoke update on public.ride_bookings from anon, authenticated;
grant update (status) on public.ride_bookings to authenticated;

create policy rides_select on public.rides
  for select to authenticated
  using (true);

create policy rides_insert on public.rides
  for insert to authenticated
  with check (driver_id = auth.uid());

create policy rides_update on public.rides
  for update to authenticated
  using (driver_id = auth.uid())
  with check (driver_id = auth.uid());

create policy rides_delete on public.rides
  for delete to authenticated
  using (driver_id = auth.uid());

create policy bookings_select on public.ride_bookings
  for select to authenticated
  using (passenger_id = auth.uid() or private.is_driver(ride_id));

create policy bookings_insert on public.ride_bookings
  for insert to authenticated
  with check (
    passenger_id = auth.uid()
    and status = 'requested'
    and not private.is_driver(ride_id)
  );

create policy bookings_update on public.ride_bookings
  for update to authenticated
  using (private.is_driver(ride_id) and private.ride_upcoming(ride_id))
  with check (
    private.is_driver(ride_id)
    and (status <> 'confirmed' or coalesce(private.seats_left(ride_id), 0) > 0)
  );

create policy bookings_delete on public.ride_bookings
  for delete to authenticated
  using (passenger_id = auth.uid() and private.ride_upcoming(ride_id));
