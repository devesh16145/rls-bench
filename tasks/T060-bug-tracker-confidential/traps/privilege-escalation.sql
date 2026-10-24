create schema private;

grant usage on schema private to authenticated;

create function private.project_role(p_project_id bigint) returns text
language sql stable security definer set search_path = ''
as $$
  select m.role from public.project_members m where m.project_id = p_project_id and m.user_id = auth.uid()
$$;

create function private.issue_confidential(p_issue_id bigint) returns boolean
language sql stable security definer set search_path = ''
as $$
  select i.is_confidential from public.issues i where i.id = p_issue_id
$$;

alter table public.projects enable row level security;
alter table public.project_members enable row level security;
alter table public.issues enable row level security;

create policy projects_select on public.projects
  for select to authenticated
  using (private.project_role(id) is not null);

create policy project_members_select on public.project_members
  for select to authenticated
  using (private.project_role(project_id) is not null);

create policy issues_select on public.issues
  for select to authenticated
  using (
    private.project_role(project_id) is not null
    and (
      not is_confidential
      or private.project_role(project_id) = 'maintainer'
      or reporter_id = auth.uid()
      or assignee_id = auth.uid()
    )
  );

create policy issues_insert on public.issues
  for insert to authenticated
  with check (reporter_id = auth.uid() and status = 'open' and private.project_role(project_id) is not null);

create policy issues_update on public.issues
  for update to authenticated
  using (private.project_role(project_id) in ('developer', 'maintainer'))
  with check (private.project_role(project_id) in ('developer', 'maintainer'));
