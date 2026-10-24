insert into auth.users (id, email) values
  ('00000000-0000-0000-0000-000000000001', 'doc1@example.com'),
  ('00000000-0000-0000-0000-000000000002', 'doc2@example.com'),
  ('00000000-0000-0000-0000-000000000003', 'aud@example.com');

insert into public.clinicians (user_id) values ('00000000-0000-0000-0000-000000000001'), ('00000000-0000-0000-0000-000000000002');
insert into public.auditors (user_id) values ('00000000-0000-0000-0000-000000000003');

insert into public.patients (id, name) values (1, 'Patient A'), (2, 'Patient B');
insert into public.care_team (patient_id, clinician_id) values (1, '00000000-0000-0000-0000-000000000001');

insert into public.medical_records (id, patient_id, note) values
  (1, 1, 'Allergic to penicillin'),
  (2, 2, 'Type 1 diabetes');

insert into public.break_glass_grants (id, patient_id, clinician_id, reason, expires_at, created_at) values
  (1, 2, '00000000-0000-0000-0000-000000000002', 'Night shift emergency', '2020-01-01 01:00+00', '2020-01-01 00:00+00');

select setval(pg_get_serial_sequence('public.break_glass_grants', 'id'), 1);
