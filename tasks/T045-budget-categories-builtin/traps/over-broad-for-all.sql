alter table public.categories enable row level security;

create policy categories_all on public.categories
  for all to authenticated
  using (user_id is null or user_id = auth.uid())
  with check (user_id = auth.uid());
