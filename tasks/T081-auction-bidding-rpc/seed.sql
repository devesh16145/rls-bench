insert into auth.users (id, email) values
  ('00000000-0000-0000-0000-000000000001', 'sel@example.com'),
  ('00000000-0000-0000-0000-000000000002', 'b1@example.com'),
  ('00000000-0000-0000-0000-000000000003', 'b2@example.com');

insert into public.auctions (id, seller_id, title, starting_price, min_increment, ends_at, highest_bid, highest_bidder) values
  (1, '00000000-0000-0000-0000-000000000001', 'Vintage watch', 100, 10, '2099-01-01', 150, '00000000-0000-0000-0000-000000000002'),
  (2, '00000000-0000-0000-0000-000000000001', 'Old radio', 50, 5, '2020-01-01', null, null),
  (3, '00000000-0000-0000-0000-000000000001', 'Signed cricket bat', 200, 25, '2099-01-01', null, null);

insert into public.bids (id, auction_id, bidder_id, amount) values (1, 1, '00000000-0000-0000-0000-000000000002', 150);

select setval(pg_get_serial_sequence('public.bids', 'id'), 1);
