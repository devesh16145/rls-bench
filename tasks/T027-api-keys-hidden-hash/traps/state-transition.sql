alter table public.api_keys enable row level security;

revoke select, insert, update, delete on public.api_keys from anon, authenticated;
grant select (id, user_id, name, last4, created_at, revoked_at) on public.api_keys to authenticated;
grant update (revoked_at) on public.api_keys to authenticated;

create policy api_keys_select on public.api_keys
  for select to authenticated
  using (user_id = auth.uid());

create policy api_keys_update on public.api_keys
  for update to authenticated
  using (user_id = auth.uid())
  with check (user_id = auth.uid() and revoked_at is not null);
