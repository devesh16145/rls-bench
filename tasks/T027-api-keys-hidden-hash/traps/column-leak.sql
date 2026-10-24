alter table public.api_keys enable row level security;

create policy api_keys_select on public.api_keys
  for select to authenticated
  using (user_id = auth.uid());

create policy api_keys_update on public.api_keys
  for update to authenticated
  using (user_id = auth.uid() and revoked_at is null)
  with check (user_id = auth.uid() and revoked_at is not null);
