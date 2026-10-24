alter table public.user_settings enable row level security;

create policy user_settings_select on public.user_settings
  for select to authenticated
  using (user_id = auth.uid());

create policy user_settings_insert on public.user_settings
  for insert to authenticated
  with check (user_id = auth.uid());

create policy user_settings_update on public.user_settings
  for update to authenticated
  using (user_id = auth.uid())
  with check (user_id = auth.uid());

create policy user_settings_delete on public.user_settings
  for delete to authenticated
  using (user_id = auth.uid());
