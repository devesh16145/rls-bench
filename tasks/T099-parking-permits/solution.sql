create schema private;

grant usage on schema private to authenticated;

create function private.lives_in(p_unit_id bigint) returns boolean
language sql stable security definer set search_path = ''
as $$
  select exists (select 1 from public.residents r where r.unit_id = p_unit_id and r.user_id = auth.uid())
$$;

create function private.is_hoa_admin() returns boolean
language sql stable security definer set search_path = ''
as $$
  select exists (select 1 from public.hoa_admins a where a.user_id = auth.uid())
$$;

create function private.active_permits(p_unit_id bigint) returns integer
language sql stable security definer set search_path = ''
as $$
  select count(*)::integer from public.permits p where p.unit_id = p_unit_id and not p.revoked and p.valid_until >= current_date
$$;

create function private.permit_revoked(p_permit_id bigint) returns boolean
language sql stable security definer set search_path = ''
as $$
  select p.revoked from public.permits p where p.id = p_permit_id
$$;

alter table public.residents enable row level security;
alter table public.hoa_admins enable row level security;
alter table public.permits enable row level security;

revoke update on public.permits from anon, authenticated;
grant update (plate, revoked) on public.permits to authenticated;

create policy residents_select on public.residents
  for select to authenticated
  using (user_id = auth.uid());

create policy permits_select on public.permits
  for select to authenticated
  using (private.lives_in(unit_id) or private.is_hoa_admin());

create policy permits_insert on public.permits
  for insert to authenticated
  with check (
    private.lives_in(unit_id)
    and not revoked
    and valid_until <= current_date + 365
    and private.active_permits(unit_id) < 2
  );

create policy permits_resident_update on public.permits
  for update to authenticated
  using (private.lives_in(unit_id))
  with check (private.lives_in(unit_id) and revoked = private.permit_revoked(id));

create policy permits_admin_update on public.permits
  for update to authenticated
  using (private.is_hoa_admin())
  with check (private.is_hoa_admin() and revoked);
