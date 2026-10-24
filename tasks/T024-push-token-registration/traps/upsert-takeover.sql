alter table public.push_tokens enable row level security;

create policy push_tokens_all on public.push_tokens
  for all to authenticated
  using (true)
  with check (user_id = auth.uid());
