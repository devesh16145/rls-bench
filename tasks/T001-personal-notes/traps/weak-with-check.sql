alter table public.notes enable row level security;

create policy notes_select on public.notes
  for select to authenticated
  using (user_id = auth.uid() or is_public);

create policy notes_insert on public.notes
  for insert to authenticated
  with check (user_id = auth.uid());

create policy notes_update on public.notes
  for update to authenticated
  using (user_id = auth.uid())
  with check (true);

create policy notes_delete on public.notes
  for delete to authenticated
  using (user_id = auth.uid());
