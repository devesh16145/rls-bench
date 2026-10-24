insert into auth.users (id, email) values
  ('00000000-0000-0000-0000-000000000001', 'sal@example.com'),
  ('00000000-0000-0000-0000-000000000002', 'bea@example.com'),
  ('00000000-0000-0000-0000-000000000003', 'mo@example.com');

insert into public.moderators (user_id) values ('00000000-0000-0000-0000-000000000003');

insert into public.listings (id, seller_id, title, price, status, is_flagged, deleted_at) values
  (1, '00000000-0000-0000-0000-000000000001', 'Road bike', 15000, 'active', false, null),
  (2, '00000000-0000-0000-0000-000000000001', 'Standing desk', 9000, 'draft', false, null),
  (3, '00000000-0000-0000-0000-000000000001', 'Designer watch', 500, 'active', true, null),
  (4, '00000000-0000-0000-0000-000000000001', 'Old sofa', 2000, 'active', false, '2020-03-01'),
  (5, '00000000-0000-0000-0000-000000000002', 'Brass lamp', 1200, 'active', false, null),
  (6, '00000000-0000-0000-0000-000000000002', 'Bookshelf', 3000, 'draft', false, null);

select setval(pg_get_serial_sequence('public.listings', 'id'), 6);
