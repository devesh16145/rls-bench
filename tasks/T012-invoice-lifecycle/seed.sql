insert into auth.users (id, email) values
  ('00000000-0000-0000-0000-000000000001', 'ana@example.com'),
  ('00000000-0000-0000-0000-000000000002', 'ben@example.com'),
  ('00000000-0000-0000-0000-000000000003', 'fin@example.com'),
  ('00000000-0000-0000-0000-000000000004', 'dee@example.com');

insert into public.finance_staff (user_id) values
  ('00000000-0000-0000-0000-000000000003');

insert into public.invoices (id, created_by, customer, amount, status) values
  (1, '00000000-0000-0000-0000-000000000001', 'Acme', 100.00, 'draft'),
  (2, '00000000-0000-0000-0000-000000000001', 'Globex', 250.00, 'sent'),
  (3, '00000000-0000-0000-0000-000000000002', 'Initech', 75.00, 'paid'),
  (4, '00000000-0000-0000-0000-000000000002', 'Umbrella', 500.00, 'sent');

select setval(pg_get_serial_sequence('public.invoices', 'id'), 4);
