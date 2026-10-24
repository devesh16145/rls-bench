insert into auth.users (id, email) values
  ('00000000-0000-0000-0000-000000000001', 'ana@example.com'),
  ('00000000-0000-0000-0000-000000000002', 'ben@example.com'),
  ('00000000-0000-0000-0000-000000000003', 'cy@example.com'),
  ('00000000-0000-0000-0000-000000000004', 'dee@example.com'),
  ('00000000-0000-0000-0000-000000000005', 'eli@example.com');

insert into public.orgs (id, name) values
  (1, 'Northwind'),
  (2, 'Contoso');

insert into public.org_members (org_id, user_id, role) values
  (1, '00000000-0000-0000-0000-000000000001', 'admin'),
  (1, '00000000-0000-0000-0000-000000000002', 'member'),
  (1, '00000000-0000-0000-0000-000000000004', 'member'),
  (2, '00000000-0000-0000-0000-000000000003', 'admin'),
  (2, '00000000-0000-0000-0000-000000000004', 'member');

insert into public.projects (id, org_id, name) values
  (10, 1, 'Website'),
  (11, 1, 'Mobile app'),
  (20, 2, 'ERP rollout');

insert into storage.buckets (id, name, public) values
  ('project-files', 'project-files', false),
  ('avatars', 'avatars', true);

insert into storage.objects (bucket_id, name, owner) values
  ('project-files', '10/spec.pdf', '00000000-0000-0000-0000-000000000001'),
  ('project-files', '11/plan.md', '00000000-0000-0000-0000-000000000001'),
  ('project-files', '20/budget.xlsx', '00000000-0000-0000-0000-000000000003'),
  ('project-files', 'readme.txt', null),
  ('avatars', '00000000-0000-0000-0000-000000000001/me.png', '00000000-0000-0000-0000-000000000001'),
  ('avatars', '00000000-0000-0000-0000-000000000003/me.png', '00000000-0000-0000-0000-000000000003');
