insert into auth.users (id, email) values
  ('00000000-0000-0000-0000-000000000001', 'tia@example.com'),
  ('00000000-0000-0000-0000-000000000002', 'rev@example.com'),
  ('00000000-0000-0000-0000-000000000003', 'tam@example.com');

insert into public.projects (id, name) values (1, 'Checkout app');

insert into public.translators (project_id, user_id, lang, role) values
  (1, '00000000-0000-0000-0000-000000000001', 'hi', 'translator'), (1, '00000000-0000-0000-0000-000000000002', 'hi', 'reviewer'), (1, '00000000-0000-0000-0000-000000000003', 'ta', 'translator');

insert into public.segments (id, project_id, lang, source_text, target_text, status, translated_by) values
  (1, 1, 'hi', 'Pay now', null, 'draft', null),
  (2, 1, 'hi', 'Cancel', 'रद्द करें', 'reviewed', '00000000-0000-0000-0000-000000000001'),
  (3, 1, 'ta', 'Pay now', null, 'draft', null);
