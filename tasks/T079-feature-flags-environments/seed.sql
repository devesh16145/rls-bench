insert into auth.users (id, email) values
  ('00000000-0000-0000-0000-000000000001', 'dev1@example.com'),
  ('00000000-0000-0000-0000-000000000002', 'adm@example.com'),
  ('00000000-0000-0000-0000-000000000003', 'dev2@example.com');

insert into public.orgs (id, name) values (1, 'Acme'), (2, 'Globex');

insert into public.org_members (org_id, user_id, role) values
  (1, '00000000-0000-0000-0000-000000000001', 'developer'), (1, '00000000-0000-0000-0000-000000000002', 'admin'), (2, '00000000-0000-0000-0000-000000000003', 'developer');

insert into public.flags (id, org_id, env, key, enabled) values
  (1, 1, 'dev', 'new-ui', false),
  (2, 1, 'prod', 'new-ui', false),
  (3, 2, 'prod', 'beta-search', true);

select setval(pg_get_serial_sequence('public.flags', 'id'), 3);
