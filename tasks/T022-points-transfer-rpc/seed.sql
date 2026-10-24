insert into auth.users (id, email) values
  ('00000000-0000-0000-0000-000000000001', 'ana@example.com'),
  ('00000000-0000-0000-0000-000000000002', 'ben@example.com'),
  ('00000000-0000-0000-0000-000000000003', 'cy@example.com'),
  ('00000000-0000-0000-0000-000000000004', 'dee@example.com');

insert into public.wallets (user_id, balance) values
  ('00000000-0000-0000-0000-000000000001', 100),
  ('00000000-0000-0000-0000-000000000002', 20),
  ('00000000-0000-0000-0000-000000000003', 0);

insert into public.transfers (id, from_user, to_user, amount) values
  (1, '00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000002', 30);

select setval(pg_get_serial_sequence('public.transfers', 'id'), 1);
