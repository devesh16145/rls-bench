alter table public.subscriptions enable row level security;

create policy subscriptions_insert on public.subscriptions
  for insert to anon, authenticated
  with check (true);

create policy subscriptions_select on public.subscriptions
  for select to authenticated
  using (lower(email) = lower(auth.jwt() ->> 'email'));

create policy subscriptions_delete on public.subscriptions
  for delete to authenticated
  using (lower(email) = lower(auth.jwt() ->> 'email'));
