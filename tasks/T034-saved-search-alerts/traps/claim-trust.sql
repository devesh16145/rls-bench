alter table public.saved_searches enable row level security;

create policy saved_searches_select on public.saved_searches
  for select to authenticated
  using (user_id = auth.uid());

create policy saved_searches_insert on public.saved_searches
  for insert to authenticated
  with check (
    user_id = auth.uid()
    and (notify_email is null or lower(notify_email) = lower(coalesce(auth.jwt() -> 'user_metadata' ->> 'email', auth.jwt() ->> 'email')))
  );

create policy saved_searches_update on public.saved_searches
  for update to authenticated
  using (user_id = auth.uid())
  with check (
    user_id = auth.uid()
    and (notify_email is null or lower(notify_email) = lower(coalesce(auth.jwt() -> 'user_metadata' ->> 'email', auth.jwt() ->> 'email')))
  );

create policy saved_searches_delete on public.saved_searches
  for delete to authenticated
  using (user_id = auth.uid());
