insert into auth.users (id, email) values
  ('00000000-0000-0000-0000-000000000001', 'ana@example.com'),
  ('00000000-0000-0000-0000-000000000002', 'ben@example.com');

insert into public.guestbook_entries (id, author_id, display_name, message, is_approved) values
  (1, '00000000-0000-0000-0000-000000000001', 'Ana', 'Great talk last week', true),
  (2, null, 'Guest', 'Hello from Pune', true),
  (3, null, 'Cheap pills', 'buy now!!!', false),
  (4, '00000000-0000-0000-0000-000000000002', 'Ben', 'Nice photos', false);

select setval(pg_get_serial_sequence('public.guestbook_entries', 'id'), 4);
