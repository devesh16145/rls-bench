insert into auth.users (id, email) values
  ('00000000-0000-0000-0000-000000000001', 'staff@example.com'),
  ('00000000-0000-0000-0000-000000000002', 'ben@example.com');

insert into public.contact_messages (id, name, email, body, status, handled_by) values
  (1, 'Rita', 'rita@example.org', 'Do you ship to Goa?', 'handled', '00000000-0000-0000-0000-000000000001'),
  (2, 'Sam', 'sam@example.org', 'Invoice question', 'new', null);

select setval(pg_get_serial_sequence('public.contact_messages', 'id'), 2);
