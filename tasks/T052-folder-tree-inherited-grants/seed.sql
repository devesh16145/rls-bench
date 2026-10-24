insert into auth.users (id, email) values
  ('00000000-0000-0000-0000-000000000001', 'ana@example.com'),
  ('00000000-0000-0000-0000-000000000002', 'ben@example.com'),
  ('00000000-0000-0000-0000-000000000003', 'hal@example.com'),
  ('00000000-0000-0000-0000-000000000004', 'mia@example.com'),
  ('00000000-0000-0000-0000-000000000005', 'pat@example.com');

insert into public.folders (id, parent_id, owner_id, name) values
  (1, null, '00000000-0000-0000-0000-000000000001', 'Company'),
  (2, 1, '00000000-0000-0000-0000-000000000001', 'HR'),
  (3, 2, '00000000-0000-0000-0000-000000000001', 'Payroll'),
  (4, 1, '00000000-0000-0000-0000-000000000001', 'Marketing'),
  (5, null, '00000000-0000-0000-0000-000000000002', 'Ben private'),
  (6, 4, '00000000-0000-0000-0000-000000000001', 'Campaigns');

insert into public.folder_grants (folder_id, user_id, can_edit) values
  (2, '00000000-0000-0000-0000-000000000003', false),
  (4, '00000000-0000-0000-0000-000000000004', true),
  (2, '00000000-0000-0000-0000-000000000004', false),
  (3, '00000000-0000-0000-0000-000000000005', false);

insert into public.documents (id, folder_id, title) values
  (1, 1, 'Employee handbook'),
  (2, 2, 'Leave policy'),
  (3, 3, 'Salaries 2020'),
  (4, 4, 'Brand guide'),
  (5, 5, 'Ben notes');

select setval(pg_get_serial_sequence('public.folders', 'id'), 6);
select setval(pg_get_serial_sequence('public.documents', 'id'), 5);
