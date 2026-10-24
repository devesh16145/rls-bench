alter table public.decks enable row level security;
alter table public.cards enable row level security;

create policy decks_select on public.decks
  for select to anon, authenticated
  using (is_public or owner_id = auth.uid());

create policy decks_insert on public.decks
  for insert to authenticated
  with check (owner_id = auth.uid());

create policy decks_update on public.decks
  for update to authenticated
  using (owner_id = auth.uid())
  with check (owner_id = auth.uid());

create policy decks_delete on public.decks
  for delete to authenticated
  using (owner_id = auth.uid());

create policy cards_select on public.cards
  for select to anon, authenticated
  using (true);

create policy cards_insert on public.cards
  for insert to authenticated
  with check (exists (select 1 from public.decks d where d.id = deck_id and d.owner_id = auth.uid()));

create policy cards_update on public.cards
  for update to authenticated
  using (exists (select 1 from public.decks d where d.id = deck_id and d.owner_id = auth.uid()))
  with check (exists (select 1 from public.decks d where d.id = deck_id and d.owner_id = auth.uid()));

create policy cards_delete on public.cards
  for delete to authenticated
  using (exists (select 1 from public.decks d where d.id = deck_id and d.owner_id = auth.uid()));
