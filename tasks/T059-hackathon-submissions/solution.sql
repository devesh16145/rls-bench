create schema private;

grant usage on schema private to authenticated;

create function private.is_member(p_team_id bigint) returns boolean
language sql stable security definer set search_path = ''
as $$
  select exists (select 1 from public.team_members m where m.team_id = p_team_id and m.user_id = auth.uid())
$$;

create function private.team_open(p_team_id bigint) returns boolean
language sql stable security definer set search_path = ''
as $$
  select coalesce((select e.deadline > now() from public.teams t join public.events e on e.id = t.event_id where t.id = p_team_id), false)
$$;

create function private.judge_can_see(p_team_id bigint) returns boolean
language sql stable security definer set search_path = ''
as $$
  select exists (
    select 1 from public.teams t
    join public.events e on e.id = t.event_id
    join public.judges j on j.event_id = e.id
    where t.id = p_team_id and j.user_id = auth.uid() and e.deadline <= now()
  )
$$;

alter table public.events enable row level security;
alter table public.teams enable row level security;
alter table public.team_members enable row level security;
alter table public.judges enable row level security;
alter table public.submissions enable row level security;

create policy events_select on public.events
  for select to authenticated
  using (true);

create policy teams_select on public.teams
  for select to authenticated
  using (true);

create policy team_members_select on public.team_members
  for select to authenticated
  using (user_id = auth.uid());

create policy submissions_select on public.submissions
  for select to authenticated
  using (private.is_member(team_id) or private.judge_can_see(team_id));

create policy submissions_insert on public.submissions
  for insert to authenticated
  with check (private.is_member(team_id) and private.team_open(team_id));

create policy submissions_update on public.submissions
  for update to authenticated
  using (private.is_member(team_id) and private.team_open(team_id))
  with check (private.is_member(team_id) and private.team_open(team_id));
