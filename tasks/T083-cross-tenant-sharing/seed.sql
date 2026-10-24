insert into auth.users (id, email) values
  ('00000000-0000-0000-0000-000000000001', 'acme_admin@example.com'),
  ('00000000-0000-0000-0000-000000000002', 'acme_member@example.com'),
  ('00000000-0000-0000-0000-000000000003', 'glob_admin@example.com'),
  ('00000000-0000-0000-0000-000000000004', 'glob_member@example.com'),
  ('00000000-0000-0000-0000-000000000005', 'eve@example.com');

insert into public.items (id, tenant_id, title) values
  (1, 'acme', 'Wholesale price list'),
  (2, 'acme', 'Partner roadmap'),
  (3, 'globex', 'Design kit');

insert into public.item_shares (item_id, target_tenant, expires_at) values
  (1, 'globex', null),
  (2, 'globex', '2020-01-01');

select setval(pg_get_serial_sequence('public.items', 'id'), 3);
