insert into auth.users (id, email) values
  ('00000000-0000-0000-0000-000000000001', 'ph1@example.com'),
  ('00000000-0000-0000-0000-000000000002', 'ph2@example.com'),
  ('00000000-0000-0000-0000-000000000003', 'pam@example.com'),
  ('00000000-0000-0000-0000-000000000004', 'pete@example.com');

insert into public.pharmacists (user_id) values ('00000000-0000-0000-0000-000000000001'), ('00000000-0000-0000-0000-000000000002');

insert into public.prescriptions (id, patient_id, drug, refills_left, expires_at) values
  (1, '00000000-0000-0000-0000-000000000003', 'Metformin 500mg', 2, '2099-01-01'),
  (2, '00000000-0000-0000-0000-000000000003', 'Amoxicillin 250mg', 0, '2099-01-01'),
  (3, '00000000-0000-0000-0000-000000000003', 'Ibuprofen 400mg', 3, '2020-01-01'),
  (4, '00000000-0000-0000-0000-000000000002', 'Atorvastatin 10mg', 1, '2099-01-01'),
  (5, '00000000-0000-0000-0000-000000000004', 'Salbutamol inhaler', 5, '2099-01-01');

insert into public.dispenses (id, prescription_id, pharmacist_id) values (1, 1, '00000000-0000-0000-0000-000000000001');

select setval(pg_get_serial_sequence('public.dispenses', 'id'), 1);
