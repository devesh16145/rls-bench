insert into auth.users (id, email) values
  ('00000000-0000-0000-0000-000000000001', 'ana@example.com'),
  ('00000000-0000-0000-0000-000000000002', 'ben@example.com'),
  ('00000000-0000-0000-0000-000000000003', 'cy@example.com'),
  ('00000000-0000-0000-0000-000000000004', 'dee@example.com'),
  ('00000000-0000-0000-0000-000000000005', 'eli@example.com');

insert into public.teams (id, name) values
  (1, 'Acme'),
  (2, 'Globex');

insert into public.team_members (team_id, user_id, role) values
  (1, '00000000-0000-0000-0000-000000000001', 'editor'),
  (2, '00000000-0000-0000-0000-000000000001', 'viewer'),
  (1, '00000000-0000-0000-0000-000000000002', 'editor'),
  (1, '00000000-0000-0000-0000-000000000003', 'viewer'),
  (2, '00000000-0000-0000-0000-000000000004', 'editor');

insert into public.documents (id, team_id, title, created_by, deleted_at) values
  (1, 1, 'Roadmap', '00000000-0000-0000-0000-000000000001', null),
  (2, 1, 'Budget', '00000000-0000-0000-0000-000000000002', null),
  (3, 2, 'Hiring plan', '00000000-0000-0000-0000-000000000004', null),
  (4, 1, 'Old pricing', '00000000-0000-0000-0000-000000000002', '2020-01-01'),
  (5, 2, 'Launch notes', '00000000-0000-0000-0000-000000000004', null);

select setval(pg_get_serial_sequence('public.documents', 'id'), 5);
