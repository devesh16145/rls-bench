insert into auth.users (id, email) values
  ('00000000-0000-0000-0000-000000000001', 'ana@example.com'),
  ('00000000-0000-0000-0000-000000000002', 'ben@example.com'),
  ('00000000-0000-0000-0000-000000000003', 'cy@example.com'),
  ('00000000-0000-0000-0000-000000000004', 'dee@example.com'),
  ('00000000-0000-0000-0000-000000000005', 'eli@example.com');

insert into public.orgs (id, name, created_by) values
  (1, 'Northwind', '00000000-0000-0000-0000-000000000001'),
  (2, 'Contoso', '00000000-0000-0000-0000-000000000005');

insert into public.org_members (org_id, user_id, role) values
  (1, '00000000-0000-0000-0000-000000000001', 'owner'),
  (1, '00000000-0000-0000-0000-000000000002', 'admin'),
  (1, '00000000-0000-0000-0000-000000000003', 'member'),
  (2, '00000000-0000-0000-0000-000000000003', 'owner');

select setval(pg_get_serial_sequence('public.orgs', 'id'), 2);
