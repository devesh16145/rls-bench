insert into auth.users (id, email) values
  ('00000000-0000-0000-0000-000000000001', 'pa@example.com'),
  ('00000000-0000-0000-0000-000000000002', 'ma@example.com'),
  ('00000000-0000-0000-0000-000000000003', 'kid1@example.com'),
  ('00000000-0000-0000-0000-000000000004', 'kid2@example.com'),
  ('00000000-0000-0000-0000-000000000005', 'pz@example.com'),
  ('00000000-0000-0000-0000-000000000006', 'kz@example.com');

insert into public.households (id, name) values (1, 'Sharma family'), (2, 'Iyer family');

insert into public.household_members (household_id, user_id, role) values
  (1, '00000000-0000-0000-0000-000000000001', 'parent'), (1, '00000000-0000-0000-0000-000000000002', 'parent'), (1, '00000000-0000-0000-0000-000000000003', 'child'), (1, '00000000-0000-0000-0000-000000000004', 'child'),
  (2, '00000000-0000-0000-0000-000000000005', 'parent'), (2, '00000000-0000-0000-0000-000000000006', 'child');

insert into public.chores (id, household_id, title, assignee_id, points, status) values
  (1, 1, 'Make the bed', '00000000-0000-0000-0000-000000000003', 10, 'todo'),
  (2, 1, 'Feed the cat', '00000000-0000-0000-0000-000000000004', 5, 'done'),
  (3, 1, 'Clean room', '00000000-0000-0000-0000-000000000003', 20, 'approved'),
  (4, 2, 'Homework', '00000000-0000-0000-0000-000000000006', 7, 'todo');

select setval(pg_get_serial_sequence('public.chores', 'id'), 4);
