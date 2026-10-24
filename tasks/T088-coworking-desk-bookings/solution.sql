create schema private;

grant usage on schema private to authenticated;

create function private.membership_ok(p_desk_id bigint, p_day date) returns boolean
language sql stable security definer set search_path = ''
as $$
  select exists (
    select 1 from public.memberships m join public.desks d on d.id = p_desk_id
    where m.user_id = auth.uid()
      and p_day <= m.valid_until
      and (d.zone = 'standard' or m.tier = 'premium')
  )
$$;

create function private.upcoming_bookings() returns integer
language sql stable security definer set search_path = ''
as $$
  select count(*)::integer from public.bookings b where b.user_id = auth.uid() and b.day >= current_date
$$;

alter table public.desks enable row level security;
alter table public.memberships enable row level security;
alter table public.bookings enable row level security;

create policy desks_select on public.desks
  for select to authenticated
  using (true);

create policy memberships_select on public.memberships
  for select to authenticated
  using (user_id = auth.uid());

create policy bookings_select on public.bookings
  for select to authenticated
  using (true);

create policy bookings_insert on public.bookings
  for insert to authenticated
  with check (
    user_id = auth.uid()
    and day >= current_date
    and private.membership_ok(desk_id, day)
    and private.upcoming_bookings() < 3
  );

create policy bookings_delete on public.bookings
  for delete to authenticated
  using (user_id = auth.uid() and day >= current_date);
