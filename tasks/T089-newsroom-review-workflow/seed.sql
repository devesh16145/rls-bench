insert into auth.users (id, email) values
  ('00000000-0000-0000-0000-000000000001', 'wen@example.com'),
  ('00000000-0000-0000-0000-000000000002', 'wes@example.com'),
  ('00000000-0000-0000-0000-000000000003', 'ed@example.com');

insert into public.editors (user_id) values ('00000000-0000-0000-0000-000000000003');

insert into public.articles (id, author_id, title, status, published_at) values
  (1, '00000000-0000-0000-0000-000000000001', 'City budget explained', 'draft', null),
  (2, '00000000-0000-0000-0000-000000000001', 'Metro line opens', 'in_review', null),
  (3, '00000000-0000-0000-0000-000000000002', 'Election results', 'published', '2020-03-01'),
  (4, '00000000-0000-0000-0000-000000000002', 'Cricket preview', 'draft', null);

select setval(pg_get_serial_sequence('public.articles', 'id'), 4);
