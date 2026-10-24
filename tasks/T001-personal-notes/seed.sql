insert into auth.users (id, email) values
  ('00000000-0000-0000-0000-000000000001', 'ana@example.com'),
  ('00000000-0000-0000-0000-000000000002', 'ben@example.com'),
  ('00000000-0000-0000-0000-000000000003', 'cy@example.com');

insert into public.notes (id, user_id, body, is_public) values
  (1, '00000000-0000-0000-0000-000000000001', 'ana private', false),
  (2, '00000000-0000-0000-0000-000000000001', 'ana public', true),
  (3, '00000000-0000-0000-0000-000000000002', 'ben private', false),
  (4, '00000000-0000-0000-0000-000000000002', 'ben public', true);

select setval(pg_get_serial_sequence('public.notes', 'id'), 4);
