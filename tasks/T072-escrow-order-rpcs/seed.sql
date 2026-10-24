insert into auth.users (id, email) values
  ('00000000-0000-0000-0000-000000000001', 'sel@example.com'),
  ('00000000-0000-0000-0000-000000000002', 'buy@example.com'),
  ('00000000-0000-0000-0000-000000000003', 'oth@example.com');

insert into public.listings (id, seller_id, title, price) values
  (1, '00000000-0000-0000-0000-000000000001', 'Vintage camera', 500),
  (2, '00000000-0000-0000-0000-000000000001', 'Mechanical keyboard', 1200);

insert into public.orders (id, listing_id, buyer_id, seller_id, amount, status) values
  (1, 1, '00000000-0000-0000-0000-000000000002', '00000000-0000-0000-0000-000000000001', 500, 'paid'),
  (2, 2, '00000000-0000-0000-0000-000000000002', '00000000-0000-0000-0000-000000000001', 1200, 'shipped'),
  (3, 1, '00000000-0000-0000-0000-000000000002', '00000000-0000-0000-0000-000000000001', 500, 'pending_payment'),
  (4, 2, '00000000-0000-0000-0000-000000000002', '00000000-0000-0000-0000-000000000001', 1200, 'released');

select setval(pg_get_serial_sequence('public.orders', 'id'), 4);
