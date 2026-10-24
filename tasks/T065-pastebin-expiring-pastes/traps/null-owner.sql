alter table public.pastes enable row level security;

create policy pastes_select on public.pastes
  for select to anon, authenticated
  using (
    (not is_private and (expires_at is null or expires_at > now()))
    or author_id = auth.uid()
  );

create policy pastes_insert on public.pastes
  for insert to anon, authenticated
  with check (author_id is not distinct from auth.uid() and (author_id is not null or not is_private));

create policy pastes_delete on public.pastes
  for delete to anon, authenticated
  using (author_id is not distinct from auth.uid());
