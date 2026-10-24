insert into auth.users (id, email) values
  ('00000000-0000-0000-0000-000000000001', 'mae@example.com'),
  ('00000000-0000-0000-0000-000000000002', 'dan@example.com'),
  ('00000000-0000-0000-0000-000000000003', 'rey@example.com'),
  ('00000000-0000-0000-0000-000000000004', 'zed@example.com'),
  ('00000000-0000-0000-0000-000000000005', 'out@example.com');

insert into public.projects (id, name) values (1, 'Payments API');

insert into public.project_members (project_id, user_id, role) values
  (1, '00000000-0000-0000-0000-000000000001', 'maintainer'), (1, '00000000-0000-0000-0000-000000000002', 'developer'), (1, '00000000-0000-0000-0000-000000000003', 'reporter'), (1, '00000000-0000-0000-0000-000000000004', 'reporter');

insert into public.issues (id, project_id, title, reporter_id, assignee_id, status, is_confidential) values
  (1, 1, 'Typo on checkout page', '00000000-0000-0000-0000-000000000003', null, 'open', false),
  (2, 1, 'Card numbers in debug logs', '00000000-0000-0000-0000-000000000004', '00000000-0000-0000-0000-000000000002', 'open', true),
  (3, 1, 'Auth bypass on refunds', '00000000-0000-0000-0000-000000000001', null, 'open', true),
  (4, 1, 'Slow invoice export', '00000000-0000-0000-0000-000000000003', '00000000-0000-0000-0000-000000000002', 'in_progress', false);

select setval(pg_get_serial_sequence('public.issues', 'id'), 4);
