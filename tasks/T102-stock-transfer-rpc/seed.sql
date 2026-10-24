insert into auth.users (id, email) values
  ('00000000-0000-0000-0000-000000000001', 'sam@example.com'),
  ('00000000-0000-0000-0000-000000000002', 'sue@example.com');

insert into public.warehouses (id, name) values (1, 'Pune'), (2, 'Mumbai'), (3, 'Nagpur');

insert into public.warehouse_staff (warehouse_id, user_id) values (1, '00000000-0000-0000-0000-000000000001'), (2, '00000000-0000-0000-0000-000000000002');

insert into public.stock (warehouse_id, sku, qty) values (1, 'SKU-1', 10), (2, 'SKU-1', 3);
