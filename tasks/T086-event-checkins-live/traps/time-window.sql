alter table public.events enable row level security;
alter table public.checkins enable row level security;

revoke insert, update on public.checkins from anon, authenticated;
grant insert (event_id, user_id) on public.checkins to authenticated;

create policy events_select on public.events
  for select to authenticated
  using (true);

create policy checkins_select on public.checkins
  for select to authenticated
  using (user_id = auth.uid());

create policy checkins_insert on public.checkins
  for insert to authenticated
  with check (user_id = auth.uid());
