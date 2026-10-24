insert into auth.users (id, email) values
  ('00000000-0000-0000-0000-000000000001', 'ada@example.com'),
  ('00000000-0000-0000-0000-000000000002', 'bob@example.com'),
  ('00000000-0000-0000-0000-000000000003', 'cal@example.com'),
  ('00000000-0000-0000-0000-000000000004', 'dan@example.com');

insert into public.orgs (id, name) values (1, 'Northwind'), (2, 'Beta Labs');

insert into public.org_members (org_id, user_id, role) values
  (1, '00000000-0000-0000-0000-000000000001', 'admin'),
  (1, '00000000-0000-0000-0000-000000000002', 'member'),
  (2, '00000000-0000-0000-0000-000000000002', 'admin');

insert into public.invites (token, org_id, email, role, expires_at, accepted_at, invited_by) values
  ('tok-cal-member', 1, 'Cal@Example.com', 'member', '2099-01-01', null, '00000000-0000-0000-0000-000000000001'),
  ('tok-cal-expired', 1, 'cal@example.com', 'admin', '2020-01-01', null, '00000000-0000-0000-0000-000000000001'),
  ('tok-dan-used', 1, 'dan@example.com', 'member', '2099-01-01', '2020-02-01', '00000000-0000-0000-0000-000000000001'),
  ('tok-dan-admin', 1, 'dan@example.com', 'admin', '2099-01-01', null, '00000000-0000-0000-0000-000000000001'),
  ('tok-org2', 2, 'cal@example.com', 'member', '2099-01-01', null, '00000000-0000-0000-0000-000000000002');
