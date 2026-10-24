alter table public.incidents enable row level security;
alter table public.incident_updates enable row level security;

create policy incidents_select on public.incidents
  for select to anon, authenticated
  using (is_published);

create policy incident_updates_select on public.incident_updates
  for select to anon, authenticated
  using (is_published);
