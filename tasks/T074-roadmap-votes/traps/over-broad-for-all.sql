alter table public.roadmap_items enable row level security;
alter table public.item_votes enable row level security;

create policy roadmap_items_select on public.roadmap_items
  for select to anon, authenticated
  using (true);

create policy item_votes_all on public.item_votes
  for all to authenticated
  using (true)
  with check (user_id = auth.uid());

create policy item_votes_insert on public.item_votes
  for insert to authenticated
  with check (
    user_id = auth.uid()
    and exists (select 1 from public.roadmap_items i where i.id = item_id and i.status <> 'shipped')
  );
