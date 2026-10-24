insert into auth.users (id, email) values
  ('00000000-0000-0000-0000-000000000001', 'ed@example.com'),
  ('00000000-0000-0000-0000-000000000002', 'ana@example.com'),
  ('00000000-0000-0000-0000-000000000003', 'ben@example.com');

insert into public.editors (user_id) values ('00000000-0000-0000-0000-000000000001');

insert into public.pages (slug, title, body, is_protected, updated_by) values
  ('home', 'Welcome', 'Main page', true, '00000000-0000-0000-0000-000000000001'),
  ('faq', 'FAQ', 'Questions', false, '00000000-0000-0000-0000-000000000002'),
  ('drafts', 'Drafts', 'Scratch space', false, '00000000-0000-0000-0000-000000000003');

insert into public.page_revisions (id, slug, body, author_id) values
  (1, 'home', 'Main page', '00000000-0000-0000-0000-000000000001'),
  (2, 'faq', 'Questions', '00000000-0000-0000-0000-000000000002');

select setval(pg_get_serial_sequence('public.page_revisions', 'id'), 2);
