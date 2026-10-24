insert into auth.users (id, email) values
  ('00000000-0000-0000-0000-000000000001', 'hal@example.com'),
  ('00000000-0000-0000-0000-000000000002', 'ana@example.com'),
  ('00000000-0000-0000-0000-000000000003', 'ben@example.com'),
  ('00000000-0000-0000-0000-000000000004', 'cy@example.com'),
  ('00000000-0000-0000-0000-000000000005', 'dee@example.com');

insert into public.events (id, host_id, title, is_private, capacity) values
  (1, '00000000-0000-0000-0000-000000000001', 'Postgres meetup', false, 2),
  (2, '00000000-0000-0000-0000-000000000001', 'Team dinner', true, 3),
  (3, '00000000-0000-0000-0000-000000000001', 'Hands-on workshop', false, 1);

insert into public.invites (event_id, user_id) values
  (2, '00000000-0000-0000-0000-000000000002'),
  (2, '00000000-0000-0000-0000-000000000003');

insert into public.rsvps (event_id, user_id) values
  (1, '00000000-0000-0000-0000-000000000002'),
  (2, '00000000-0000-0000-0000-000000000002'),
  (3, '00000000-0000-0000-0000-000000000003');
