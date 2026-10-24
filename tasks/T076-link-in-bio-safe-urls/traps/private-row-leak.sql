alter table public.bio_links enable row level security;

create policy bio_links_select on public.bio_links
  for select to anon, authenticated
  using (true);

create policy bio_links_insert on public.bio_links
  for insert to authenticated
  with check (user_id = auth.uid() and url like 'https://%');

create policy bio_links_update on public.bio_links
  for update to authenticated
  using (user_id = auth.uid())
  with check (user_id = auth.uid() and url like 'https://%');

create policy bio_links_delete on public.bio_links
  for delete to authenticated
  using (user_id = auth.uid());
