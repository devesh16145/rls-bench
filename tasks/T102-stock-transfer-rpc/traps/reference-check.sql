create schema private;

grant usage on schema private to authenticated;

create function private.is_staff(p_warehouse_id bigint) returns boolean
language sql stable security definer set search_path = ''
as $$
  select exists (select 1 from public.warehouse_staff s where s.warehouse_id = p_warehouse_id and s.user_id = auth.uid())
$$;

alter table public.warehouses enable row level security;
alter table public.warehouse_staff enable row level security;
alter table public.stock enable row level security;
alter table public.transfers enable row level security;

create policy warehouses_select on public.warehouses
  for select to authenticated
  using (true);

create policy stock_select on public.stock
  for select to authenticated
  using (private.is_staff(warehouse_id));

create policy transfers_select on public.transfers
  for select to authenticated
  using (private.is_staff(from_warehouse) or private.is_staff(to_warehouse));

create function public.transfer_stock(p_from bigint, p_to bigint, p_sku text, p_qty integer) returns integer
language plpgsql security definer set search_path = ''
as $$
declare
  v_uid uuid := auth.uid();
  v_left integer;
begin
  if v_uid is null or not exists (select 1 from public.warehouse_staff s where s.user_id = v_uid) then
    raise exception 'only staff of the source warehouse can transfer';
  end if;
  if p_qty is null or p_qty <= 0 then
    raise exception 'quantity must be positive';
  end if;
  if p_from = p_to or not exists (select 1 from public.warehouses w where w.id = p_to) then
    raise exception 'invalid destination';
  end if;
  update public.stock set qty = qty - p_qty
  where warehouse_id = p_from and sku = p_sku and qty >= p_qty
  returning qty into v_left;
  if not found then
    raise exception 'not enough stock';
  end if;
  insert into public.stock (warehouse_id, sku, qty) values (p_to, p_sku, p_qty)
  on conflict (warehouse_id, sku) do update set qty = public.stock.qty + excluded.qty;
  insert into public.transfers (from_warehouse, to_warehouse, sku, qty, moved_by)
  values (p_from, p_to, p_sku, p_qty, v_uid);
  return v_left;
end
$$;
