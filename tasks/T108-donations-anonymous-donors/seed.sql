insert into auth.users (id, email) values
  ('00000000-0000-0000-0000-000000000001', 'o1@example.com'),
  ('00000000-0000-0000-0000-000000000002', 'd1@example.com'),
  ('00000000-0000-0000-0000-000000000003', 'd2@example.com');

insert into public.campaigns (id, title, owner_id, status) values
  (1, 'New roof for the shelter', '00000000-0000-0000-0000-000000000001', 'active'),
  (2, 'Winter coats 2019', '00000000-0000-0000-0000-000000000001', 'closed'),
  (3, 'Community garden', '00000000-0000-0000-0000-000000000002', 'active');

insert into public.donations (id, campaign_id, donor_id, amount_cents, anonymous, message) values
  (1, 1, '00000000-0000-0000-0000-000000000002', 500, false, 'Good luck'),
  (2, 1, '00000000-0000-0000-0000-000000000003', 700, true, ''),
  (3, 2, '00000000-0000-0000-0000-000000000003', 300, false, 'Stay warm'),
  (4, 3, '00000000-0000-0000-0000-000000000003', 100, true, '');

select setval(pg_get_serial_sequence('public.campaigns', 'id'), 3);
select setval(pg_get_serial_sequence('public.donations', 'id'), 4);
