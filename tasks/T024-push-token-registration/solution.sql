alter table public.push_tokens enable row level security;

create policy push_tokens_select on public.push_tokens
  for select to authenticated
  using (user_id = auth.uid());

create policy push_tokens_insert on public.push_tokens
  for insert to authenticated
  with check (user_id = auth.uid());

create policy push_tokens_update on public.push_tokens
  for update to authenticated
  using (user_id = auth.uid())
  with check (user_id = auth.uid());

create policy push_tokens_delete on public.push_tokens
  for delete to authenticated
  using (user_id = auth.uid());
