create schema private;

grant usage on schema private to authenticated;

create function private.is_staff() returns boolean
language sql stable security definer set search_path = ''
as $$
  select exists (select 1 from public.staff s where s.user_id = auth.uid())
$$;

create function private.is_project_client(p_project_id bigint) returns boolean
language sql stable security definer set search_path = ''
as $$
  select exists (select 1 from public.projects p where p.id = p_project_id and p.client_id = auth.uid())
$$;

alter table public.staff enable row level security;
alter table public.projects enable row level security;
alter table public.project_comments enable row level security;

create policy staff_select on public.staff
  for select to authenticated
  using (user_id = auth.uid());

create policy projects_select on public.projects
  for select to authenticated
  using (client_id = auth.uid() or private.is_staff());

create policy comments_select on public.project_comments
  for select to authenticated
  using (private.is_staff() or (not is_internal and private.is_project_client(project_id)));

create policy comments_insert on public.project_comments
  for insert to authenticated
  with check (
    author_id = auth.uid()
    and (private.is_staff() or private.is_project_client(project_id))
  );

create policy comments_update on public.project_comments
  for update to authenticated
  using (author_id = auth.uid())
  with check (
    author_id = auth.uid()
    and (private.is_staff() or (not is_internal and private.is_project_client(project_id)))
  );

create policy comments_delete on public.project_comments
  for delete to authenticated
  using (author_id = auth.uid());
