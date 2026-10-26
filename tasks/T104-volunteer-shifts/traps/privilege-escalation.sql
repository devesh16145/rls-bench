create schema private;

grant usage on schema private to authenticated;

create function private.is_coordinator() returns boolean
language sql stable security definer set search_path = ''
as $$
  select exists (select 1 from public.coordinators c where c.user_id = auth.uid())
$$;

create function private.shift_open_future(p_shift_id bigint) returns boolean
language sql stable security definer set search_path = ''
as $$
  select exists (select 1 from public.shifts s where s.id = p_shift_id and s.status = 'open' and s.starts_at > now())
$$;

create function private.shift_has_room(p_shift_id bigint) returns boolean
language sql stable security definer set search_path = ''
as $$
  select (select count(*) from public.signups g where g.shift_id = p_shift_id and g.status = 'active') < (select s.capacity from public.shifts s where s.id = p_shift_id)
$$;

create function private.already_signed_up(p_shift_id bigint) returns boolean
language sql stable security definer set search_path = ''
as $$
  select exists (select 1 from public.signups g where g.shift_id = p_shift_id and g.volunteer_id = auth.uid() and g.status = 'active')
$$;

alter table public.coordinators enable row level security;
alter table public.shifts enable row level security;
alter table public.signups enable row level security;

revoke update on public.signups from anon, authenticated;
grant update (status) on public.signups to authenticated;

create policy coordinators_select on public.coordinators
  for select to authenticated
  using (user_id = auth.uid());

create policy shifts_select on public.shifts
  for select to authenticated
  using (status <> 'cancelled' or private.is_coordinator());

create policy shifts_insert on public.shifts
  for insert to authenticated
  with check (created_by = auth.uid());

create policy shifts_update on public.shifts
  for update to authenticated
  using (private.is_coordinator())
  with check (private.is_coordinator());

create policy signups_select on public.signups
  for select to authenticated
  using (volunteer_id = auth.uid() or private.is_coordinator());

create policy signups_insert on public.signups
  for insert to authenticated
  with check (
    volunteer_id = auth.uid()
    and status = 'active'
    and private.shift_open_future(shift_id)
    and private.shift_has_room(shift_id)
    and not private.already_signed_up(shift_id)
  );

create policy signups_update on public.signups
  for update to authenticated
  using (volunteer_id = auth.uid() and status = 'active')
  with check (volunteer_id = auth.uid() and status = 'cancelled');
