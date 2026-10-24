alter table public.notes enable row level security;

create policy notes_all on public.notes
  for all to authenticated
  using (user_id = auth.uid() or is_public)
  with check (user_id = auth.uid());
