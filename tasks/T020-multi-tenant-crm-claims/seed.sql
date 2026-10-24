insert into auth.users (id, email) values
  ('00000000-0000-0000-0000-000000000001', 'ana@example.com'),
  ('00000000-0000-0000-0000-000000000002', 'ben@example.com'),
  ('00000000-0000-0000-0000-000000000003', 'cy@example.com'),
  ('00000000-0000-0000-0000-000000000004', 'dee@example.com'),
  ('00000000-0000-0000-0000-000000000005', 'eve@example.com');

insert into public.contacts (id, tenant_id, owner_id, name, is_archived) values
  (1, 'acme', '00000000-0000-0000-0000-000000000002', 'Lena Ortiz', false),
  (2, 'acme', '00000000-0000-0000-0000-000000000001', 'Mo Haddad', false),
  (3, 'acme', '00000000-0000-0000-0000-000000000002', 'Old lead', true),
  (4, 'globex', '00000000-0000-0000-0000-000000000003', 'Zed Kim', false);

insert into public.tenant_settings (tenant_id, plan, sso_required) values
  ('acme', 'pro', true),
  ('globex', 'free', false);

select setval(pg_get_serial_sequence('public.contacts', 'id'), 4);
