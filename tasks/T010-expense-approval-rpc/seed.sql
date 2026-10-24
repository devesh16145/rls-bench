insert into auth.users (id, email) values
  ('00000000-0000-0000-0000-000000000001', 'mia@example.com'),
  ('00000000-0000-0000-0000-000000000002', 'tom@example.com'),
  ('00000000-0000-0000-0000-000000000003', 'zoe@example.com'),
  ('00000000-0000-0000-0000-000000000004', 'raj@example.com'),
  ('00000000-0000-0000-0000-000000000005', 'kai@example.com'),
  ('00000000-0000-0000-0000-000000000006', 'eli@example.com');

insert into public.departments (id, name) values
  (1, 'Engineering'),
  (2, 'Marketing');

insert into public.department_members (department_id, user_id, is_manager) values
  (1, '00000000-0000-0000-0000-000000000001', true),
  (1, '00000000-0000-0000-0000-000000000002', false),
  (1, '00000000-0000-0000-0000-000000000003', false),
  (2, '00000000-0000-0000-0000-000000000004', true),
  (2, '00000000-0000-0000-0000-000000000005', false);

insert into public.expenses (id, department_id, submitted_by, amount, status, decided_by) values
  (1, 1, '00000000-0000-0000-0000-000000000002', 42.00, 'pending', null),
  (2, 1, '00000000-0000-0000-0000-000000000001', 100.00, 'pending', null),
  (3, 1, '00000000-0000-0000-0000-000000000003', 15.50, 'pending', null),
  (4, 1, '00000000-0000-0000-0000-000000000002', 60.00, 'approved', '00000000-0000-0000-0000-000000000001'),
  (5, 2, '00000000-0000-0000-0000-000000000005', 80.00, 'pending', null);

select setval(pg_get_serial_sequence('public.expenses', 'id'), 5);
