alter table public.products enable row level security;
alter table public.purchases enable row level security;
alter table public.reviews enable row level security;

create policy products_select on public.products
  for select to anon, authenticated
  using (true);

create policy purchases_select on public.purchases
  for select to authenticated
  using (user_id = auth.uid());

create policy reviews_select on public.reviews
  for select to anon, authenticated
  using (true);

create policy reviews_insert on public.reviews
  for insert to authenticated
  with check (
    user_id = auth.uid()
    and exists (select 1 from public.purchases p where p.user_id = auth.uid() and p.product_id = reviews.product_id)
  );

create policy reviews_update on public.reviews
  for update to authenticated
  using (user_id = auth.uid())
  with check (user_id = auth.uid());

create policy reviews_delete on public.reviews
  for delete to authenticated
  using (user_id = auth.uid());
