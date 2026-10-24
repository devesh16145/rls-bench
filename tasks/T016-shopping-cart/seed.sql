insert into auth.users (id, email) values
  ('00000000-0000-0000-0000-000000000001', 'ana@example.com'),
  ('00000000-0000-0000-0000-000000000002', 'ben@example.com');

insert into public.products (id, name, price, is_active) values
  (1, 'Masala chai', 4.50, true),
  (2, 'Ceramic mug', 12.00, true),
  (3, 'Old kettle', 30.00, false);

insert into public.cart_items (user_id, product_id, quantity) values
  ('00000000-0000-0000-0000-000000000001', 1, 2),
  ('00000000-0000-0000-0000-000000000002', 2, 1);
