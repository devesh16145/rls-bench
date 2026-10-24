insert into auth.users (id, email) values
  ('00000000-0000-0000-0000-000000000001', 'sam@example.com'),
  ('00000000-0000-0000-0000-000000000002', 'sue@example.com'),
  ('00000000-0000-0000-0000-000000000003', 'aud@example.com'),
  ('00000000-0000-0000-0000-000000000004', 'eve@example.com');

insert into public.locations (id, name, is_frozen) values (1, 'Pune warehouse', false), (2, 'Delhi warehouse', true);

insert into public.location_staff (location_id, user_id) values (1, '00000000-0000-0000-0000-000000000001'), (2, '00000000-0000-0000-0000-000000000002');

insert into public.stock (location_id, sku, qty) values
  (1, 'SKU-1', 10), (1, 'SKU-2', 5), (2, 'SKU-1', 7);
