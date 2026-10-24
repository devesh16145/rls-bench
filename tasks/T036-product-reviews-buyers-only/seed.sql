insert into auth.users (id, email) values
  ('00000000-0000-0000-0000-000000000001', 'ana@example.com'),
  ('00000000-0000-0000-0000-000000000002', 'ben@example.com'),
  ('00000000-0000-0000-0000-000000000003', 'cy@example.com');

insert into public.products (id, name) values (1, 'Electric kettle'), (2, 'Ceramic mug');

insert into public.purchases (user_id, product_id) values
  ('00000000-0000-0000-0000-000000000001', 1), ('00000000-0000-0000-0000-000000000001', 2), ('00000000-0000-0000-0000-000000000002', 1);

insert into public.reviews (product_id, user_id, rating, body, is_featured) values
  (1, '00000000-0000-0000-0000-000000000002', 4, 'Boils fast', true);
