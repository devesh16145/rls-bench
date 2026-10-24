insert into auth.users (id, email) values
  ('00000000-0000-0000-0000-000000000001', 'ana@example.com'),
  ('00000000-0000-0000-0000-000000000002', 'ben@example.com');

insert into public.categories (id, user_id, name, color) values
  (1, null, 'Food', '#e76f51'),
  (2, null, 'Rent', '#264653'),
  (3, '00000000-0000-0000-0000-000000000001', 'Coffee', '#6f4e37'),
  (4, '00000000-0000-0000-0000-000000000002', 'Golf', '#2d6a4f');

select setval(pg_get_serial_sequence('public.categories', 'id'), 4);
