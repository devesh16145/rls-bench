alter table public.app_config enable row level security;
alter table public.user_flag_overrides enable row level security;

create policy app_config_select on public.app_config
  for select to anon, authenticated
  using (is_public);

create policy overrides_select on public.user_flag_overrides
  for select to authenticated
  using (user_id = auth.uid());

create policy overrides_insert on public.user_flag_overrides
  for insert to authenticated
  with check (
    user_id = auth.uid()
    and exists (select 1 from public.app_config c where c.key = user_flag_overrides.key and c.is_public and c.user_overridable)
  );

create policy overrides_delete on public.user_flag_overrides
  for delete to authenticated
  using (user_id = auth.uid());
