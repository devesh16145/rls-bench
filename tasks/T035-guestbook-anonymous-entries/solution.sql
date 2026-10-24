alter table public.guestbook_entries enable row level security;

create policy guestbook_select on public.guestbook_entries
  for select to anon, authenticated
  using (is_approved or author_id = auth.uid());

create policy guestbook_insert on public.guestbook_entries
  for insert to anon, authenticated
  with check (not is_approved and author_id is not distinct from auth.uid());

create policy guestbook_delete on public.guestbook_entries
  for delete to authenticated
  using (author_id = auth.uid());
