insert into auth.users (id, email) values
  ('00000000-0000-0000-0000-000000000001', 'ana@example.com'),
  ('00000000-0000-0000-0000-000000000002', 'ben@example.com'),
  ('00000000-0000-0000-0000-000000000003', 'cy@example.com'),
  ('00000000-0000-0000-0000-000000000004', 'dee@example.com');

insert into public.friendships (requester_id, addressee_id, status) values
  ('00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000002', 'accepted'),
  ('00000000-0000-0000-0000-000000000003', '00000000-0000-0000-0000-000000000001', 'pending'),
  ('00000000-0000-0000-0000-000000000004', '00000000-0000-0000-0000-000000000003', 'accepted');

insert into public.posts (id, author_id, body, audience) values
  (1, '00000000-0000-0000-0000-000000000001', 'Hello world', 'public'),
  (2, '00000000-0000-0000-0000-000000000001', 'Moving next month', 'friends'),
  (3, '00000000-0000-0000-0000-000000000001', 'Note to self', 'only_me'),
  (4, '00000000-0000-0000-0000-000000000002', 'Party on Friday', 'friends'),
  (5, '00000000-0000-0000-0000-000000000003', 'New job!', 'friends'),
  (6, '00000000-0000-0000-0000-000000000004', 'Sunset photo', 'public');

select setval(pg_get_serial_sequence('public.posts', 'id'), 6);
