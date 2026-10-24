create schema private;

grant usage on schema private to authenticated;

create function private.lives_in(p_unit_id bigint) returns boolean
language sql stable security definer set search_path = ''
as $$
  select exists (select 1 from public.residents r where r.unit_id = p_unit_id and r.user_id = auth.uid())
$$;

create function private.staffs_unit(p_unit_id bigint) returns boolean
language sql stable security definer set search_path = ''
as $$
  select exists (select 1 from public.units u join public.building_staff s on s.building_id = u.building_id where u.id = p_unit_id and s.user_id = auth.uid())
$$;

create function private.can_see_request(p_request_id bigint) returns boolean
language sql stable security definer set search_path = ''
as $$
  select exists (select 1 from public.requests q where q.id = p_request_id and (private.lives_in(q.unit_id) or private.staffs_unit(q.unit_id)))
$$;

alter table public.units enable row level security;
alter table public.residents enable row level security;
alter table public.building_staff enable row level security;
alter table public.requests enable row level security;
alter table public.request_photos enable row level security;

revoke update on public.requests from anon, authenticated;
grant update (status) on public.requests to authenticated;

create policy units_select on public.units
  for select to authenticated
  using (private.lives_in(id) or private.staffs_unit(id));

create policy residents_select on public.residents
  for select to authenticated
  using (user_id = auth.uid());

create policy building_staff_select on public.building_staff
  for select to authenticated
  using (user_id = auth.uid());

create policy requests_select on public.requests
  for select to authenticated
  using (private.lives_in(unit_id) or private.staffs_unit(unit_id));

create policy requests_insert on public.requests
  for insert to authenticated
  with check (created_by = auth.uid() and status = 'open');

create policy requests_update on public.requests
  for update to authenticated
  using (private.staffs_unit(unit_id))
  with check (private.staffs_unit(unit_id));

create policy request_photos_select on public.request_photos
  for select to authenticated
  using (private.can_see_request(request_id));

create policy request_photos_insert on public.request_photos
  for insert to authenticated
  with check (private.can_see_request(request_id));
