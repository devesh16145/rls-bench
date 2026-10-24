alter table public.subscriptions enable row level security;

create policy subscriptions_insert on public.subscriptions
  for insert to anon, authenticated
  with check (not confirmed);

create policy subscriptions_select on public.subscriptions
  for select to authenticated
  using (lower(email) = lower(coalesce(auth.jwt() -> 'user_metadata' ->> 'email', auth.jwt() ->> 'email')));

create policy subscriptions_delete on public.subscriptions
  for delete to authenticated
  using (lower(email) = lower(auth.jwt() ->> 'email'));
