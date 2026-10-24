insert into auth.users (id, email) values
  ('00000000-0000-0000-0000-000000000001', 'ana@example.com'),
  ('00000000-0000-0000-0000-000000000002', 'ben@example.com');

insert into public.notifications (id, user_id, title, body, read_at) values
  (1, '00000000-0000-0000-0000-000000000001', 'Your invoice is ready', 'Invoice #1042 is available.', null),
  (2, '00000000-0000-0000-0000-000000000001', 'Password changed', 'If this was not you, contact support.', '2020-01-05'),
  (3, '00000000-0000-0000-0000-000000000002', 'New login from Pune', 'A new device signed in.', null);

select setval(pg_get_serial_sequence('public.notifications', 'id'), 3);
