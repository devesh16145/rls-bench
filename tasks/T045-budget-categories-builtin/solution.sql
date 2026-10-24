alter table public.categories enable row level security;

create policy categories_select on public.categories
  for select to authenticated
  using (user_id is null or user_id = auth.uid());

create policy categories_insert on public.categories
  for insert to authenticated
  with check (user_id = auth.uid());

create policy categories_update on public.categories
  for update to authenticated
  using (user_id = auth.uid())
  with check (user_id = auth.uid());

create policy categories_delete on public.categories
  for delete to authenticated
  using (user_id = auth.uid());
