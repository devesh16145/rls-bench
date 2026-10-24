alter table public.habits enable row level security;

create policy habits_select on public.habits
  for select to authenticated
  using (true);

create policy habits_insert on public.habits
  for insert to authenticated
  with check (user_id = auth.uid());

create policy habits_update on public.habits
  for update to authenticated
  using (user_id = auth.uid())
  with check (user_id = auth.uid());

create policy habits_delete on public.habits
  for delete to authenticated
  using (user_id = auth.uid());
