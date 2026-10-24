create schema private;

grant usage on schema private to authenticated;

create function private.is_member(p_org_id bigint) returns boolean
language sql stable security definer set search_path = ''
as $$
  select exists (select 1 from public.org_members m where m.org_id = p_org_id and m.user_id = auth.uid())
$$;

create function private.is_admin(p_org_id bigint) returns boolean
language sql stable security definer set search_path = ''
as $$
  select exists (select 1 from public.org_members m where m.org_id = p_org_id and m.user_id = auth.uid() and m.role = 'admin')
$$;

create function private.sso_session() returns boolean
language sql stable
as $$
  select exists (
    select 1 from jsonb_array_elements(coalesce(auth.jwt() -> 'amr', '[]'::jsonb)) as e
    where e ->> 'method' = 'sso/saml'
  ) or coalesce((auth.jwt() -> 'user_metadata' ->> 'sso')::boolean, false)
$$;

create function private.org_session_ok(p_org_id bigint) returns boolean
language sql stable security definer set search_path = ''
as $$
  select coalesce((select not o.require_sso or private.sso_session() from public.orgs o where o.id = p_org_id), false)
$$;

alter table public.orgs enable row level security;
alter table public.org_members enable row level security;
alter table public.org_documents enable row level security;

create policy orgs_select on public.orgs
  for select to authenticated
  using (private.is_member(id) and (not require_sso or private.sso_session()));

create policy orgs_update on public.orgs
  for update to authenticated
  using (private.is_admin(id) and (not require_sso or private.sso_session()))
  with check (private.is_admin(id));

create policy org_members_select on public.org_members
  for select to authenticated
  using (private.is_member(org_id) and private.org_session_ok(org_id));

create policy documents_session on public.org_documents
  as restrictive
  for all to authenticated
  using (private.org_session_ok(org_id))
  with check (private.org_session_ok(org_id));

create policy documents_select on public.org_documents
  for select to authenticated
  using (private.is_member(org_id));

create policy documents_insert on public.org_documents
  for insert to authenticated
  with check (private.is_admin(org_id));

create policy documents_update on public.org_documents
  for update to authenticated
  using (private.is_admin(org_id))
  with check (private.is_admin(org_id));

create policy documents_delete on public.org_documents
  for delete to authenticated
  using (private.is_admin(org_id));
