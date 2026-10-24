insert into auth.users (id, email) values
  ('00000000-0000-0000-0000-000000000001', 'ana@example.com'),
  ('00000000-0000-0000-0000-000000000002', 'ben@example.com'),
  ('00000000-0000-0000-0000-000000000003', 'tara@example.com'),
  ('00000000-0000-0000-0000-000000000004', 'cy@example.com');

insert into public.courses (id, name) values (1, 'Databases 101'), (2, 'Statistics');

insert into public.enrollments (course_id, user_id, role) values
  (1, '00000000-0000-0000-0000-000000000001', 'student'), (1, '00000000-0000-0000-0000-000000000002', 'student'), (1, '00000000-0000-0000-0000-000000000003', 'ta'), (2, '00000000-0000-0000-0000-000000000004', 'student');

insert into public.threads (id, course_id, title, created_by, is_locked) values
  (1, 1, 'Week 1 questions', '00000000-0000-0000-0000-000000000001', false),
  (2, 1, 'Exam rules', '00000000-0000-0000-0000-000000000003', true),
  (3, 2, 'Introductions', '00000000-0000-0000-0000-000000000004', false);

insert into public.posts (id, thread_id, author_id, body) values
  (1, 1, '00000000-0000-0000-0000-000000000001', 'What is a foreign key?'),
  (2, 1, '00000000-0000-0000-0000-000000000002', 'A column that references another table.'),
  (3, 2, '00000000-0000-0000-0000-000000000003', 'Closed book, 2 hours.'),
  (4, 3, '00000000-0000-0000-0000-000000000004', 'Hi all!');

select setval(pg_get_serial_sequence('public.threads', 'id'), 3);
select setval(pg_get_serial_sequence('public.posts', 'id'), 4);
