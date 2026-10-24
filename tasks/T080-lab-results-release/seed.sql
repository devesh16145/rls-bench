insert into auth.users (id, email) values
  ('00000000-0000-0000-0000-000000000001', 'pam@example.com'),
  ('00000000-0000-0000-0000-000000000002', 'pete@example.com'),
  ('00000000-0000-0000-0000-000000000003', 'doc@example.com');

insert into public.patients (id, user_id) values (1, '00000000-0000-0000-0000-000000000001'), (2, '00000000-0000-0000-0000-000000000002');

insert into public.care_team (patient_id, doctor_id) values (1, '00000000-0000-0000-0000-000000000003');

insert into public.lab_results (id, patient_id, test_name, result_text, released_at) values
  (1, 1, 'HbA1c', '5.6%', '2020-02-01'),
  (2, 1, 'Lipid panel', 'LDL 160 mg/dL', null),
  (3, 1, 'Biopsy', 'Benign', '2099-01-01'),
  (4, 2, 'CBC', 'Normal', '2020-03-01');

select setval(pg_get_serial_sequence('public.lab_results', 'id'), 4);
