create schema private;

grant usage on schema private to authenticated;

create function private.is_assigned(p_project_id bigint) returns boolean
language sql stable security definer set search_path = ''
as $$
  select exists (select 1 from public.assignments a where a.project_id = p_project_id and a.user_id = auth.uid())
$$;

create function private.period_open(p_period_id bigint) returns boolean
language sql stable security definer set search_path = ''
as $$
  select coalesce((select not p.is_locked from public.periods p where p.id = p_period_id), false)
$$;

alter table public.projects enable row level security;
alter table public.assignments enable row level security;
alter table public.periods enable row level security;
alter table public.time_entries enable row level security;

create policy projects_select on public.projects
  for select to authenticated
  using (private.is_assigned(id));

create policy assignments_select on public.assignments
  for select to authenticated
  using (user_id = auth.uid());

create policy periods_select on public.periods
  for select to authenticated
  using (true);

create policy time_entries_select on public.time_entries
  for select to authenticated
  using (user_id = auth.uid());

create policy time_entries_insert on public.time_entries
  for insert to authenticated
  with check (user_id = auth.uid() and private.period_open(period_id));

create policy time_entries_update on public.time_entries
  for update to authenticated
  using (user_id = auth.uid() and private.period_open(period_id))
  with check (user_id = auth.uid() and private.is_assigned(project_id) and private.period_open(period_id));

create policy time_entries_delete on public.time_entries
  for delete to authenticated
  using (user_id = auth.uid() and private.period_open(period_id));
