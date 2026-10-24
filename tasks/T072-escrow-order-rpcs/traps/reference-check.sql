alter table public.listings enable row level security;
alter table public.orders enable row level security;

create policy listings_select on public.listings
  for select to authenticated
  using (true);

create policy orders_select on public.orders
  for select to authenticated
  using (buyer_id = auth.uid() or seller_id = auth.uid());

create policy orders_insert on public.orders
  for insert to authenticated
  with check (
    buyer_id = auth.uid()
    and status = 'pending_payment'
  );

create function public.mark_shipped(p_order_id bigint) returns text
language plpgsql security definer set search_path = ''
as $$
declare
  v_order public.orders%rowtype;
begin
  select * into v_order from public.orders where id = p_order_id for update;
  if not found then
    raise exception 'unknown order';
  end if;
  if auth.uid() is null or v_order.seller_id <> auth.uid() then
    raise exception 'only the seller can mark an order shipped';
  end if;
  if v_order.status not in ('paid') then
    raise exception 'order is %, cannot move to shipped', v_order.status;
  end if;
  update public.orders set status = 'shipped' where id = p_order_id;
  return 'shipped';
end
$$;

create function public.release_funds(p_order_id bigint) returns text
language plpgsql security definer set search_path = ''
as $$
declare
  v_order public.orders%rowtype;
begin
  select * into v_order from public.orders where id = p_order_id for update;
  if not found then
    raise exception 'unknown order';
  end if;
  if auth.uid() is null or v_order.buyer_id <> auth.uid() then
    raise exception 'only the buyer can release funds';
  end if;
  if v_order.status not in ('shipped') then
    raise exception 'order is %, cannot move to released', v_order.status;
  end if;
  update public.orders set status = 'released' where id = p_order_id;
  return 'released';
end
$$;

create function public.refund_order(p_order_id bigint) returns text
language plpgsql security definer set search_path = ''
as $$
declare
  v_order public.orders%rowtype;
begin
  select * into v_order from public.orders where id = p_order_id for update;
  if not found then
    raise exception 'unknown order';
  end if;
  if auth.uid() is null or v_order.seller_id <> auth.uid() then
    raise exception 'only the seller can refund';
  end if;
  if v_order.status not in ('paid', 'shipped') then
    raise exception 'order is %, cannot move to refunded', v_order.status;
  end if;
  update public.orders set status = 'refunded' where id = p_order_id;
  return 'refunded';
end
$$;
