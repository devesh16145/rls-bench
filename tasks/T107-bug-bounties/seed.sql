insert into auth.users (id, email) values
  ('00000000-0000-0000-0000-000000000001', 'p1@example.com'),
  ('00000000-0000-0000-0000-000000000002', 's1@example.com'),
  ('00000000-0000-0000-0000-000000000003', 's2@example.com'),
  ('00000000-0000-0000-0000-000000000004', 's3@example.com'),
  ('00000000-0000-0000-0000-000000000005', 's4@example.com');

insert into public.bounties (id, title, poster_id, status, awarded_submission_id) values
  (1, 'Find the auth bypass', '00000000-0000-0000-0000-000000000001', 'open', null),
  (2, 'Explain the slow query', '00000000-0000-0000-0000-000000000001', 'awarded', 3),
  (3, 'Crash on upload', '00000000-0000-0000-0000-000000000003', 'open', null);

insert into public.submissions (id, bounty_id, submitter_id, body) values
  (1, 1, '00000000-0000-0000-0000-000000000002', 'Token is reused after logout'),
  (2, 1, '00000000-0000-0000-0000-000000000003', 'Session cookie not cleared'),
  (3, 2, '00000000-0000-0000-0000-000000000002', 'Missing index on created_at'),
  (4, 3, '00000000-0000-0000-0000-000000000002', 'Null filename'),
  (5, 2, '00000000-0000-0000-0000-000000000004', 'Sequential scan');

select setval(pg_get_serial_sequence('public.bounties', 'id'), 3);
select setval(pg_get_serial_sequence('public.submissions', 'id'), 5);
