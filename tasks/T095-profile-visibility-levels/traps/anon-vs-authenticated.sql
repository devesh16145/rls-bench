alter table public.profiles enable row level security;

create policy profiles_select_public on public.profiles
  for select to anon, authenticated
  using (visibility in ('public', 'members'));

create policy profiles_select_members on public.profiles
  for select to authenticated
  using (visibility = 'members' or user_id = auth.uid());

create policy profiles_insert on public.profiles
  for insert to authenticated
  with check (user_id = auth.uid());

create policy profiles_update on public.profiles
  for update to authenticated
  using (user_id = auth.uid())
  with check (user_id = auth.uid());

create policy profiles_delete on public.profiles
  for delete to authenticated
  using (user_id = auth.uid());
