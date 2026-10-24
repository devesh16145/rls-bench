alter table public.events enable row level security;
alter table public.checkins enable row level security;

create policy events_select on public.events
  for select to authenticated
  using (true);

create policy checkins_select on public.checkins
  for select to authenticated
  using (user_id = auth.uid());

create policy checkins_insert on public.checkins
  for insert to authenticated
  with check (
    user_id = auth.uid()
    and exists (select 1 from public.events e where e.id = event_id and e.starts_at <= now() and e.ends_at >= now())
  );
