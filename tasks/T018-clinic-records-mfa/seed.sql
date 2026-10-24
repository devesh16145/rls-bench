insert into auth.users (id, email) values
  ('00000000-0000-0000-0000-000000000001', 'pam@example.com'),
  ('00000000-0000-0000-0000-000000000002', 'pete@example.com'),
  ('00000000-0000-0000-0000-000000000003', 'dia@example.com'),
  ('00000000-0000-0000-0000-000000000004', 'ed@example.com');

insert into public.patients (id, user_id, full_name) values
  (1, '00000000-0000-0000-0000-000000000001', 'Pam Rao'),
  (2, '00000000-0000-0000-0000-000000000002', 'Pete Iyer');

insert into public.care_team (patient_id, doctor_id) values
  (1, '00000000-0000-0000-0000-000000000003'),
  (2, '00000000-0000-0000-0000-000000000004');

insert into public.records (id, patient_id, author_id, note) values
  (1, 1, '00000000-0000-0000-0000-000000000003', 'Initial consult'),
  (2, 1, '00000000-0000-0000-0000-000000000003', 'Blood test ordered'),
  (3, 2, '00000000-0000-0000-0000-000000000004', 'Follow-up in 2 weeks');

select setval(pg_get_serial_sequence('public.records', 'id'), 3);
