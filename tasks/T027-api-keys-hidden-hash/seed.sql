insert into auth.users (id, email) values
  ('00000000-0000-0000-0000-000000000001', 'ana@example.com'),
  ('00000000-0000-0000-0000-000000000002', 'ben@example.com');

insert into public.api_keys (id, user_id, name, key_hash, last4, revoked_at) values
  (1, '00000000-0000-0000-0000-000000000001', 'CI', 'sha256$9f2c', 'a1b2', null),
  (2, '00000000-0000-0000-0000-000000000001', 'Laptop', 'sha256$71aa', 'c3d4', null),
  (3, '00000000-0000-0000-0000-000000000001', 'Old server', 'sha256$03be', 'e5f6', '2020-03-01'),
  (4, '00000000-0000-0000-0000-000000000002', 'Prod', 'sha256$5d10', 'g7h8', null);

select setval(pg_get_serial_sequence('public.api_keys', 'id'), 4);
