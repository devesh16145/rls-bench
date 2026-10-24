insert into auth.users (id, email) values
  ('00000000-0000-0000-0000-000000000001', 'ana@example.com'),
  ('00000000-0000-0000-0000-000000000002', 'ben@example.com');

insert into public.pastes (id, author_id, content, is_private, expires_at) values
  (1, '00000000-0000-0000-0000-000000000001', 'select 1;', false, null),
  (2, '00000000-0000-0000-0000-000000000001', 'my notes', true, null),
  (3, '00000000-0000-0000-0000-000000000001', 'old snippet', false, '2020-01-01'),
  (4, null, 'anon snippet', false, '2099-01-01'),
  (5, null, 'expired anon snippet', false, '2020-01-01'),
  (6, '00000000-0000-0000-0000-000000000002', 'ben private', true, null);

select setval(pg_get_serial_sequence('public.pastes', 'id'), 6);
