alter table public.profiles enable row level security;

create policy profiles_select on public.profiles
  for select to anon, authenticated
  using (true);

create policy profiles_insert on public.profiles
  for insert to authenticated
  with check (id = auth.uid());

create policy profiles_update on public.profiles
  for update to authenticated
  using (id = auth.uid())
  with check (id = auth.uid());
