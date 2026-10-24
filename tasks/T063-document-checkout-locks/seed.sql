insert into auth.users (id, email) values
  ('00000000-0000-0000-0000-000000000001', 'ana@example.com'),
  ('00000000-0000-0000-0000-000000000002', 'ben@example.com'),
  ('00000000-0000-0000-0000-000000000003', 'cy@example.com');

insert into public.documents (id, title, body, checked_out_by) values
  (1, 'Spec', 'v1', null),
  (2, 'Plan', 'draft', '00000000-0000-0000-0000-000000000001'),
  (3, 'Budget', 'confidential', null),
  (4, 'Contract', 'clause 1', '00000000-0000-0000-0000-000000000002');

insert into public.doc_access (doc_id, user_id, can_edit) values
  (1, '00000000-0000-0000-0000-000000000001', true), (2, '00000000-0000-0000-0000-000000000001', true), (4, '00000000-0000-0000-0000-000000000001', true),
  (1, '00000000-0000-0000-0000-000000000002', true), (3, '00000000-0000-0000-0000-000000000002', true), (4, '00000000-0000-0000-0000-000000000002', true),
  (1, '00000000-0000-0000-0000-000000000003', false);
