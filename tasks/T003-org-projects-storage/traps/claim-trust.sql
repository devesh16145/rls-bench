create schema private;

grant usage on schema private to authenticated;

create function private.is_org_member(p_org_id bigint) returns boolean
language sql stable security definer set search_path = ''
as $$
  select exists (
    select 1 from public.org_members m
    where m.org_id = p_org_id and m.user_id = auth.uid()
  )
$$;

create function private.is_org_admin(p_org_id bigint) returns boolean
language sql stable security definer set search_path = ''
as $$
  select exists (
    select 1 from public.org_members m
    where m.org_id = p_org_id and m.user_id = auth.uid() and m.role = 'admin'
  )
  or (auth.jwt() -> 'user_metadata' ->> 'role') = 'admin'
$$;

create function private.can_access_project_file(p_name text, p_admin_only boolean) returns boolean
language sql stable security definer set search_path = ''
as $$
  select exists (
    select 1
    from public.projects p
    join public.org_members m on m.org_id = p.org_id
    where p.id::text = (storage.foldername(p_name))[1]
      and m.user_id = auth.uid()
      and (not p_admin_only or m.role = 'admin')
  )
$$;

alter table public.orgs enable row level security;
alter table public.org_members enable row level security;
alter table public.projects enable row level security;

create policy orgs_select on public.orgs
  for select to authenticated
  using (private.is_org_member(id));

create policy org_members_select on public.org_members
  for select to authenticated
  using (private.is_org_member(org_id));

create policy projects_select on public.projects
  for select to authenticated
  using (private.is_org_member(org_id));

create policy projects_insert on public.projects
  for insert to authenticated
  with check (private.is_org_admin(org_id));

create policy projects_update on public.projects
  for update to authenticated
  using (private.is_org_admin(org_id))
  with check (private.is_org_admin(org_id));

create policy projects_delete on public.projects
  for delete to authenticated
  using (private.is_org_admin(org_id));

create policy project_files_select on storage.objects
  for select to authenticated
  using (bucket_id = 'project-files' and private.can_access_project_file(name, false));

create policy project_files_insert on storage.objects
  for insert to authenticated
  with check (bucket_id = 'project-files' and private.can_access_project_file(name, true));

create policy project_files_delete on storage.objects
  for delete to authenticated
  using (bucket_id = 'project-files' and private.can_access_project_file(name, true));

create policy avatars_select on storage.objects
  for select to anon, authenticated
  using (bucket_id = 'avatars');

create policy avatars_insert on storage.objects
  for insert to authenticated
  with check (bucket_id = 'avatars' and (storage.foldername(name))[1] = auth.uid()::text);
