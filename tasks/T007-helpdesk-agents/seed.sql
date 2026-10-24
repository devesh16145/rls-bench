insert into auth.users (id, email) values
  ('00000000-0000-0000-0000-000000000001', 'ana@example.com'),
  ('00000000-0000-0000-0000-000000000002', 'ben@example.com'),
  ('00000000-0000-0000-0000-000000000003', 'sam@example.com');

insert into public.profiles (id, display_name, is_agent) values
  ('00000000-0000-0000-0000-000000000001', 'Ana', false),
  ('00000000-0000-0000-0000-000000000002', 'Ben', false),
  ('00000000-0000-0000-0000-000000000003', 'Sam (Support)', true);

insert into public.tickets (id, requester_id, subject, status, assigned_agent) values
  (1, '00000000-0000-0000-0000-000000000001', 'Cannot log in', 'open', null),
  (2, '00000000-0000-0000-0000-000000000001', 'Refund request', 'closed', '00000000-0000-0000-0000-000000000003'),
  (3, '00000000-0000-0000-0000-000000000002', 'Invoice missing', 'pending', '00000000-0000-0000-0000-000000000003');

select setval(pg_get_serial_sequence('public.tickets', 'id'), 3);
