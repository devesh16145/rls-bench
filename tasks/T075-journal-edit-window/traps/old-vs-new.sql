alter table public.journal_entries enable row level security;

create policy journal_select on public.journal_entries
  for select to authenticated
  using (user_id = auth.uid());

create policy journal_insert on public.journal_entries
  for insert to authenticated
  with check (user_id = auth.uid());

create policy journal_update on public.journal_entries
  for update to authenticated
  using (user_id = auth.uid() and created_at > now() - interval '24 hours')
  with check (user_id = auth.uid());

create policy journal_delete on public.journal_entries
  for delete to authenticated
  using (user_id = auth.uid() and created_at > now() - interval '24 hours');
