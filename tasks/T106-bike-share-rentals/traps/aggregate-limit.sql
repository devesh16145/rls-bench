create schema private;

grant usage on schema private to authenticated;

create function private.is_staff() returns boolean
language sql stable security definer set search_path = ''
as $$
  select exists (select 1 from public.staff s where s.user_id = auth.uid())
$$;

create function private.bike_free(p_bike_id bigint) returns boolean
language sql stable security definer set search_path = ''
as $$
  select exists (select 1 from public.bikes b where b.id = p_bike_id and b.status = 'in_service') and not exists (select 1 from public.rentals r where r.bike_id = p_bike_id and r.returned_at is null)
$$;

create function private.has_open_rental() returns boolean
language sql stable security definer set search_path = ''
as $$
  select exists (select 1 from public.rentals r where r.user_id = auth.uid() and r.returned_at is null)
$$;

alter table public.staff enable row level security;
alter table public.bikes enable row level security;
alter table public.rentals enable row level security;

revoke insert, update on public.rentals from anon, authenticated;
grant insert (bike_id, user_id, started_at) on public.rentals to authenticated;
grant update (returned_at) on public.rentals to authenticated;

create policy staff_select on public.staff
  for select to authenticated
  using (user_id = auth.uid());

create policy bikes_select on public.bikes
  for select to authenticated
  using (true);

create policy bikes_update on public.bikes
  for update to authenticated
  using (private.is_staff())
  with check (private.is_staff());

create policy rentals_select on public.rentals
  for select to authenticated
  using (user_id = auth.uid() or private.is_staff());

create policy rentals_insert on public.rentals
  for insert to authenticated
  with check (
    user_id = auth.uid()
    and returned_at is null
    and private.bike_free(bike_id)
  );

create policy rentals_update on public.rentals
  for update to authenticated
  using (user_id = auth.uid() and returned_at is null)
  with check (user_id = auth.uid() and returned_at is not null);
