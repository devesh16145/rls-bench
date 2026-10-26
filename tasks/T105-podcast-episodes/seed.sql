insert into auth.users (id, email) values
  ('00000000-0000-0000-0000-000000000001', 'h1@example.com'),
  ('00000000-0000-0000-0000-000000000002', 'h2@example.com'),
  ('00000000-0000-0000-0000-000000000003', 'listener@example.com');

insert into public.shows (id, title) values (1, 'Database Hour'), (2, 'Ship It');

insert into public.hosts (show_id, user_id) values (1, '00000000-0000-0000-0000-000000000001'), (2, '00000000-0000-0000-0000-000000000002');

insert into public.episodes (id, show_id, title, status, publish_at, created_by) values
  (1, 1, 'Indexes', 'published', '2020-01-01 00:00+00', '00000000-0000-0000-0000-000000000001'),
  (2, 1, 'Replication', 'published', '2099-01-01 00:00+00', '00000000-0000-0000-0000-000000000001'),
  (3, 1, 'Draft about locks', 'draft', null, '00000000-0000-0000-0000-000000000001'),
  (4, 2, 'Launch day', 'published', '2020-02-01 00:00+00', '00000000-0000-0000-0000-000000000002'),
  (5, 2, 'Unfinished', 'draft', '2020-03-01 00:00+00', '00000000-0000-0000-0000-000000000002');

select setval(pg_get_serial_sequence('public.shows', 'id'), 2);
select setval(pg_get_serial_sequence('public.episodes', 'id'), 5);
