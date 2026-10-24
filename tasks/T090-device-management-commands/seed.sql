insert into auth.users (id, email) values
  ('00000000-0000-0000-0000-000000000001', 'it1@example.com'),
  ('00000000-0000-0000-0000-000000000002', 'it2@example.com'),
  ('00000000-0000-0000-0000-000000000003', 'emp1@example.com'),
  ('00000000-0000-0000-0000-000000000004', 'emp2@example.com'),
  ('00000000-0000-0000-0000-000000000005', 'emp3@example.com');

insert into public.org_admins (org_id, user_id) values (1, '00000000-0000-0000-0000-000000000001'), (2, '00000000-0000-0000-0000-000000000002');

insert into public.devices (id, org_id, assigned_to, name) values
  (1, 1, '00000000-0000-0000-0000-000000000003', 'MacBook Pro 14'),
  (2, 1, '00000000-0000-0000-0000-000000000004', 'Pixel 8'),
  (3, 2, '00000000-0000-0000-0000-000000000005', 'ThinkPad X1');

insert into public.device_commands (id, device_id, command, issued_by) values (1, 1, 'locate', '00000000-0000-0000-0000-000000000003');

select setval(pg_get_serial_sequence('public.device_commands', 'id'), 1);
