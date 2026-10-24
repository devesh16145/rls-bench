insert into auth.users (id, email) values
  ('00000000-0000-0000-0000-000000000001', 'ana@example.com'),
  ('00000000-0000-0000-0000-000000000002', 'ben@example.com'),
  ('00000000-0000-0000-0000-000000000003', 'cy@example.com'),
  ('00000000-0000-0000-0000-000000000004', 'sam@example.com'),
  ('00000000-0000-0000-0000-000000000005', 'tia@example.com');

insert into public.units (id, building_id, label) values (101, 1, 'A-101'), (102, 1, 'A-102'), (201, 2, 'B-201');

insert into public.residents (unit_id, user_id) values (101, '00000000-0000-0000-0000-000000000001'), (102, '00000000-0000-0000-0000-000000000002'), (201, '00000000-0000-0000-0000-000000000003');

insert into public.building_staff (building_id, user_id) values (1, '00000000-0000-0000-0000-000000000004'), (2, '00000000-0000-0000-0000-000000000005');

insert into public.requests (id, unit_id, created_by, description, status) values
  (1, 101, '00000000-0000-0000-0000-000000000001', 'Leaking tap', 'open'),
  (2, 102, '00000000-0000-0000-0000-000000000002', 'Broken window', 'in_progress'),
  (3, 201, '00000000-0000-0000-0000-000000000003', 'No hot water', 'open');

insert into public.request_photos (id, request_id, path) values (1, 1, 'req1/tap.jpg'), (2, 2, 'req2/window.jpg');

select setval(pg_get_serial_sequence('public.requests', 'id'), 3);
select setval(pg_get_serial_sequence('public.request_photos', 'id'), 2);
