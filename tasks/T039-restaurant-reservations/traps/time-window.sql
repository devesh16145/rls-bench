create schema private;

grant usage on schema private to authenticated;

create function private.is_staff(p_restaurant_id bigint) returns boolean
language sql stable security definer set search_path = ''
as $$
  select exists (select 1 from public.restaurant_staff s where s.restaurant_id = p_restaurant_id and s.user_id = auth.uid())
$$;

alter table public.restaurants enable row level security;
alter table public.restaurant_staff enable row level security;
alter table public.reservations enable row level security;

revoke update on public.reservations from anon, authenticated;
grant update (status) on public.reservations to authenticated;

create policy restaurants_select on public.restaurants
  for select to authenticated
  using (true);

create policy reservations_select on public.reservations
  for select to authenticated
  using (user_id = auth.uid() or private.is_staff(restaurant_id));

create policy reservations_insert on public.reservations
  for insert to authenticated
  with check (user_id = auth.uid() and status = 'booked');

create policy reservations_update on public.reservations
  for update to authenticated
  using (
    status = 'booked'
    and (
      (user_id = auth.uid() and reserved_for > now())
      or (private.is_staff(restaurant_id) and reserved_for <= now())
    )
  )
  with check (
    (user_id = auth.uid() and status = 'cancelled' and reserved_for > now())
    or (private.is_staff(restaurant_id) and status in ('seated', 'no_show') and reserved_for <= now())
  );
