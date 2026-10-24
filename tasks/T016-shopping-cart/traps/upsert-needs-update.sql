alter table public.products enable row level security;
alter table public.cart_items enable row level security;

create policy products_select on public.products
  for select to anon, authenticated
  using (is_active);

create policy cart_items_select on public.cart_items
  for select to authenticated
  using (user_id = auth.uid());

create policy cart_items_insert on public.cart_items
  for insert to authenticated
  with check (
    user_id = auth.uid()
    and exists (select 1 from public.products p where p.id = product_id and p.is_active)
  );

create policy cart_items_delete on public.cart_items
  for delete to authenticated
  using (user_id = auth.uid());
