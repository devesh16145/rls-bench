insert into auth.users (id, email) values
  ('00000000-0000-0000-0000-000000000001', 'ana@example.com'),
  ('00000000-0000-0000-0000-000000000002', 'ben@example.com'),
  ('00000000-0000-0000-0000-000000000003', 'cy@example.com');

insert into public.receipts (id, uploaded_by, merchant, amount) values
  (1, '00000000-0000-0000-0000-000000000001', 'Taxi', 12.50),
  (2, '00000000-0000-0000-0000-000000000001', 'Hotel', 180.00),
  (3, '00000000-0000-0000-0000-000000000002', 'Lunch', 22.00),
  (4, null, 'Bank fee', 3.00),
  (5, null, 'Card subscription', 9.99);

select setval(pg_get_serial_sequence('public.receipts', 'id'), 5);
