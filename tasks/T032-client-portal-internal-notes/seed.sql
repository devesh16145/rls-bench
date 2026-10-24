insert into auth.users (id, email) values
  ('00000000-0000-0000-0000-000000000001', 'sue@example.com'),
  ('00000000-0000-0000-0000-000000000002', 'sam@example.com'),
  ('00000000-0000-0000-0000-000000000003', 'cara@example.com'),
  ('00000000-0000-0000-0000-000000000004', 'carl@example.com');

insert into public.staff (user_id) values ('00000000-0000-0000-0000-000000000001'), ('00000000-0000-0000-0000-000000000002');

insert into public.projects (id, client_id, name) values
  (1, '00000000-0000-0000-0000-000000000003', 'Website redesign'),
  (2, '00000000-0000-0000-0000-000000000004', 'Mobile app');

insert into public.project_comments (id, project_id, author_id, body, is_internal) values
  (1, 1, '00000000-0000-0000-0000-000000000001', 'Kickoff done', false),
  (2, 1, '00000000-0000-0000-0000-000000000002', 'Client is slow to pay', true),
  (3, 1, '00000000-0000-0000-0000-000000000003', 'Thanks!', false),
  (4, 2, '00000000-0000-0000-0000-000000000001', 'Designs ready', false);

select setval(pg_get_serial_sequence('public.project_comments', 'id'), 4);
