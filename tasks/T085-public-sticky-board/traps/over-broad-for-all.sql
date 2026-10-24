alter table public.board_notes enable row level security;

revoke insert, update on public.board_notes from anon, authenticated;
grant insert (author_id, body, color) on public.board_notes to authenticated;
grant update (body, color) on public.board_notes to authenticated;

create policy board_notes_select on public.board_notes
  for select to anon
  using (true);

create policy board_notes_all on public.board_notes
  for all to authenticated
  using (true)
  with check (author_id = auth.uid());

create policy board_notes_insert on public.board_notes
  for insert to authenticated
  with check (author_id = auth.uid());

create policy board_notes_update on public.board_notes
  for update to authenticated
  using (author_id = auth.uid())
  with check (author_id = auth.uid());

create policy board_notes_delete on public.board_notes
  for delete to authenticated
  using (author_id = auth.uid());
