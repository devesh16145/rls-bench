insert into auth.users (id, email) values
  ('00000000-0000-0000-0000-000000000001', 'stu1@example.com'),
  ('00000000-0000-0000-0000-000000000002', 'stu2@example.com'),
  ('00000000-0000-0000-0000-000000000003', 'tut1@example.com');

insert into public.bookings (id, student_id, tutor_id, status) values
  (1, '00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000003', 'confirmed'),
  (2, '00000000-0000-0000-0000-000000000002', '00000000-0000-0000-0000-000000000003', 'cancelled'),
  (3, '00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000003', 'requested');

insert into public.booking_messages (id, booking_id, sender_id, body) values
  (1, 1, '00000000-0000-0000-0000-000000000001', 'Can we cover integrals?'),
  (2, 1, '00000000-0000-0000-0000-000000000003', 'Sure, bring your notes.'),
  (3, 2, '00000000-0000-0000-0000-000000000002', 'Sorry, need to cancel.');

select setval(pg_get_serial_sequence('public.booking_messages', 'id'), 3);
