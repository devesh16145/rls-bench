alter table public.profiles enable row level security;

create policy profiles_all on public.profiles
  for all to anon, authenticated
  using (true)
  with check (id = auth.uid());
