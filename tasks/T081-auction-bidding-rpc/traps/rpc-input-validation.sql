alter table public.auctions enable row level security;
alter table public.bids enable row level security;

create policy auctions_select on public.auctions
  for select to authenticated
  using (true);

create policy bids_select on public.bids
  for select to authenticated
  using (
    bidder_id = auth.uid()
    or exists (select 1 from public.auctions a where a.id = auction_id and a.seller_id = auth.uid())
  );

create function public.place_bid(p_auction_id bigint, p_amount numeric) returns numeric
language plpgsql security definer set search_path = ''
as $$
declare
  v_uid uuid := auth.uid();
  v_auction public.auctions%rowtype;
begin
  if v_uid is null then
    raise exception 'not signed in';
  end if;
  select * into v_auction from public.auctions where id = p_auction_id for update;
  if not found then
    raise exception 'unknown auction';
  end if;
  if v_auction.ends_at <= now() then
    raise exception 'auction has ended';
  end if;
  if v_auction.seller_id = v_uid then
    raise exception 'sellers cannot bid on their own auctions';
  end if;
  if p_amount is null or p_amount <= coalesce(v_auction.highest_bid, 0) then
    raise exception 'bid too low';
  end if;
  insert into public.bids (auction_id, bidder_id, amount) values (p_auction_id, v_uid, p_amount);
  update public.auctions set highest_bid = p_amount, highest_bidder = v_uid where id = p_auction_id;
  return p_amount;
end
$$;
