insert into auth.users (id, email) values
  ('00000000-0000-0000-0000-000000000001', 'own@example.com'),
  ('00000000-0000-0000-0000-000000000002', 'g1@example.com'),
  ('00000000-0000-0000-0000-000000000003', 'g2@example.com'),
  ('00000000-0000-0000-0000-000000000004', 'stranger@example.com');

insert into public.cameras (id, owner_id, label) values (1, '00000000-0000-0000-0000-000000000001', 'Front door'), (2, '00000000-0000-0000-0000-000000000002', 'Garage');

insert into public.camera_shares (id, camera_id, grantee_id, expires_at, created_by) values
  (1, 1, '00000000-0000-0000-0000-000000000002', '2099-01-01 00:00+00', '00000000-0000-0000-0000-000000000001'),
  (2, 1, '00000000-0000-0000-0000-000000000003', '2020-01-01 00:00+00', '00000000-0000-0000-0000-000000000001');

insert into public.stream_keys (camera_id, key) values (1, 'k1'), (2, 'k2');

select setval(pg_get_serial_sequence('public.cameras', 'id'), 2);
select setval(pg_get_serial_sequence('public.camera_shares', 'id'), 2);
