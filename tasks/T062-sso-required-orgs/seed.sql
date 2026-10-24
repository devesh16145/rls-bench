insert into auth.users (id, email) values
  ('00000000-0000-0000-0000-000000000001', 'ana@example.com'),
  ('00000000-0000-0000-0000-000000000002', 'ben@example.com'),
  ('00000000-0000-0000-0000-000000000003', 'cy@example.com');

insert into public.orgs (id, name, require_sso) values (1, 'Bank', true), (2, 'Startup', false);

insert into public.org_members (org_id, user_id, role) values
  (1, '00000000-0000-0000-0000-000000000001', 'admin'), (1, '00000000-0000-0000-0000-000000000002', 'member'), (2, '00000000-0000-0000-0000-000000000001', 'member'), (2, '00000000-0000-0000-0000-000000000003', 'admin');

insert into public.org_documents (id, org_id, title) values
  (1, 1, 'Risk report'), (2, 1, 'Audit findings'), (3, 2, 'Pitch deck');

select setval(pg_get_serial_sequence('public.org_documents', 'id'), 3);
