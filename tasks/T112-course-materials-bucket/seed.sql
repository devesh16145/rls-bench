insert into auth.users (id, email) values
  ('00000000-0000-0000-0000-000000000001', 'ins1@example.com'),
  ('00000000-0000-0000-0000-000000000002', 'ins2@example.com'),
  ('00000000-0000-0000-0000-000000000003', 'stu@example.com'),
  ('00000000-0000-0000-0000-000000000004', 'other@example.com');

insert into public.courses (id, title, instructor_id) values (1, 'Databases 101', '00000000-0000-0000-0000-000000000001'), (2, 'Distributed systems', '00000000-0000-0000-0000-000000000002');

insert into public.enrollments (course_id, student_id) values (1, '00000000-0000-0000-0000-000000000003');

insert into storage.buckets (id, name, public) values ('materials', 'materials', false), ('avatars', 'avatars', true);

insert into storage.objects (bucket_id, name, owner) values
  ('materials', '1/intro.pdf', '00000000-0000-0000-0000-000000000001'),
  ('materials', '1/lecture.mp4', '00000000-0000-0000-0000-000000000001'),
  ('materials', '2/notes.pdf', '00000000-0000-0000-0000-000000000002'),
  ('avatars', 'x.png', null);

select setval(pg_get_serial_sequence('public.courses', 'id'), 2);
