create schema private;

grant usage on schema private to authenticated;

create function private.org_role(p_org_id bigint) returns text
language sql stable security definer set search_path = ''
as $$
  select m.role from public.org_members m where m.org_id = p_org_id and m.user_id = auth.uid()
$$;

alter table public.orgs enable row level security;
alter table public.org_members enable row level security;
alter table public.flags enable row level security;

create policy orgs_select on public.orgs
  for select to authenticated
  using (private.org_role(id) is not null);

create policy org_members_select on public.org_members
  for select to authenticated
  using (private.org_role(org_id) is not null);

create policy flags_select on public.flags
  for select to authenticated
  using (private.org_role(org_id) is not null);

create policy flags_insert on public.flags
  for insert to authenticated
  with check (private.org_role(org_id) = 'admin' or (private.org_role(org_id) = 'developer' and env = 'dev'));

create policy flags_update on public.flags
  for update to authenticated
  using (private.org_role(org_id) = 'admin' or (private.org_role(org_id) = 'developer' and env = 'dev'))
  with check (private.org_role(org_id) = 'admin' or (private.org_role(org_id) = 'developer' and env = 'dev'));

create policy flags_delete on public.flags
  for delete to authenticated
  using (private.org_role(org_id) = 'admin' or (private.org_role(org_id) = 'developer' and env = 'dev'));
