insert into auth.users (id, email) values
  ('00000000-0000-0000-0000-000000000001', 'ana@example.com'),
  ('00000000-0000-0000-0000-000000000002', 'ben@example.com'),
  ('00000000-0000-0000-0000-000000000003', 'cy@example.com');

insert into public.posts (id, author_id, title, published_at, unpublish_at) values
  (1, '00000000-0000-0000-0000-000000000001', 'Hello world', '2020-01-01', null),
  (2, '00000000-0000-0000-0000-000000000001', 'Draft ideas', null, null),
  (3, '00000000-0000-0000-0000-000000000001', 'Launch day', '2099-01-01', null),
  (4, '00000000-0000-0000-0000-000000000002', 'Summer sale', '2020-01-01', '2021-01-01'),
  (5, '00000000-0000-0000-0000-000000000002', 'Changelog', '2020-01-01', '2099-01-01');

insert into public.comments (id, post_id, author_id, body) values
  (1, 1, '00000000-0000-0000-0000-000000000002', 'Welcome!'),
  (2, 1, '00000000-0000-0000-0000-000000000003', 'Nice post'),
  (3, 2, '00000000-0000-0000-0000-000000000001', 'Note to self'),
  (4, 4, '00000000-0000-0000-0000-000000000003', 'Great deal'),
  (5, 5, '00000000-0000-0000-0000-000000000001', 'Thanks for the update');

select setval(pg_get_serial_sequence('public.comments', 'id'), 5);
