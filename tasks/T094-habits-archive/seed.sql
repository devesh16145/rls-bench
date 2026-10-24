insert into auth.users (id, email) values
  ('00000000-0000-0000-0000-000000000001', 'ana@example.com'),
  ('00000000-0000-0000-0000-000000000002', 'ben@example.com');

insert into public.habits (id, user_id, name, archived_at) values
  (1, '00000000-0000-0000-0000-000000000001', 'Drink 2L water', null),
  (2, '00000000-0000-0000-0000-000000000001', 'Learn Spanish', '2020-03-01'),
  (3, '00000000-0000-0000-0000-000000000002', 'Morning run', null);

select setval(pg_get_serial_sequence('public.habits', 'id'), 3);
