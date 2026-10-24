insert into auth.users (id, email) values
  ('00000000-0000-0000-0000-000000000001', 'oli@example.com'),
  ('00000000-0000-0000-0000-000000000002', 'opa@example.com'),
  ('00000000-0000-0000-0000-000000000003', 'ozz@example.com'),
  ('00000000-0000-0000-0000-000000000004', 'rhea@example.com'),
  ('00000000-0000-0000-0000-000000000005', 'sam@example.com');

insert into public.ops_team (user_id) values ('00000000-0000-0000-0000-000000000001'), ('00000000-0000-0000-0000-000000000002'), ('00000000-0000-0000-0000-000000000003');

insert into public.access_requests (id, requester_id, resource, reason, status) values
  (1, '00000000-0000-0000-0000-000000000004', 'prod-db', 'Investigate slow query', 'pending'),
  (2, '00000000-0000-0000-0000-000000000005', 'billing-api', 'Refund a customer', 'pending'),
  (3, '00000000-0000-0000-0000-000000000001', 'prod-db', 'Run migration', 'pending'),
  (4, '00000000-0000-0000-0000-000000000004', 'logs', 'Debug incident', 'granted');

insert into public.access_approvals (id, request_id, approver_id) values
  (1, 1, '00000000-0000-0000-0000-000000000001'),
  (2, 3, '00000000-0000-0000-0000-000000000002'),
  (3, 4, '00000000-0000-0000-0000-000000000001'),
  (4, 4, '00000000-0000-0000-0000-000000000002');

select setval(pg_get_serial_sequence('public.access_requests', 'id'), 4);
select setval(pg_get_serial_sequence('public.access_approvals', 'id'), 4);
