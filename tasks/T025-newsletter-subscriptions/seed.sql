insert into auth.users (id, email) values
  ('00000000-0000-0000-0000-000000000001', 'ana@example.com'),
  ('00000000-0000-0000-0000-000000000002', 'ben@example.com');

insert into public.subscriptions (id, email, topic, confirmed) values
  (1, 'Ana@Example.com', 'weekly', true),
  (2, 'ana@example.com', 'product', false),
  (3, 'ben@example.com', 'weekly', true),
  (4, 'cy@example.com', 'weekly', true);

select setval(pg_get_serial_sequence('public.subscriptions', 'id'), 4);
