insert into auth.users (id, email) values
  ('00000000-0000-0000-0000-000000000001', 'ivy@example.com'),
  ('00000000-0000-0000-0000-000000000002', 'sam@example.com'),
  ('00000000-0000-0000-0000-000000000003', 'tia@example.com'),
  ('00000000-0000-0000-0000-000000000004', 'ola@example.com');

insert into public.courses (id, instructor_id, title, is_published) values
  (1, '00000000-0000-0000-0000-000000000001', 'SQL for analysts', true),
  (2, '00000000-0000-0000-0000-000000000001', 'Advanced Postgres', false),
  (3, '00000000-0000-0000-0000-000000000004', 'Intro to Python', true);

insert into public.lessons (id, course_id, title, is_preview) values
  (1, 1, 'Welcome', true),
  (2, 1, 'Joins in depth', false),
  (3, 2, 'Draft: partitioning', true),
  (4, 3, 'Hello Python', true);

insert into public.enrollments (course_id, student_id) values
  (1, '00000000-0000-0000-0000-000000000002');
