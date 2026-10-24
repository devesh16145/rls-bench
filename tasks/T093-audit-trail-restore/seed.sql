insert into auth.users (id, email) values
  ('00000000-0000-0000-0000-000000000001', 'adm@example.com'),
  ('00000000-0000-0000-0000-000000000002', 'mem@example.com'),
  ('00000000-0000-0000-0000-000000000003', 'oz@example.com');

insert into public.org_members (org_id, user_id, role) values (1, '00000000-0000-0000-0000-000000000001', 'admin'), (1, '00000000-0000-0000-0000-000000000002', 'member'), (2, '00000000-0000-0000-0000-000000000003', 'admin');

insert into public.records (id, org_id, title, deleted_at) values
  (1, 1, 'Vendor contract', null),
  (2, 1, 'Pricing sheet', null),
  (3, 1, 'Old memo', '2020-01-01'),
  (4, 2, 'Globex plan', null);

insert into public.audit_log (id, record_id, action, actor, at) values
  (1, 1, 'insert', '00000000-0000-0000-0000-000000000001', '2020-01-01'),
  (2, 2, 'insert', '00000000-0000-0000-0000-000000000002', '2020-01-01'),
  (3, 4, 'insert', '00000000-0000-0000-0000-000000000003', '2020-01-01');

select setval(pg_get_serial_sequence('public.records', 'id'), 4);
select setval(pg_get_serial_sequence('public.audit_log', 'id'), 3);
