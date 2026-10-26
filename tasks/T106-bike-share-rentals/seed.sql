insert into auth.users (id, email) values
  ('00000000-0000-0000-0000-000000000001', 'u1@example.com'),
  ('00000000-0000-0000-0000-000000000002', 'u2@example.com'),
  ('00000000-0000-0000-0000-000000000003', 'staff@example.com');

insert into public.staff (user_id) values ('00000000-0000-0000-0000-000000000003');

insert into public.bikes (id, label, status) values
  (1, 'Dock A-1', 'in_service'),
  (2, 'Dock A-2', 'in_service'),
  (3, 'Dock B-1', 'out_of_service');

insert into public.rentals (id, bike_id, user_id, started_at, returned_at, cost_cents) values
  (1, 2, '00000000-0000-0000-0000-000000000002', '2020-01-01 10:00+00', null, null),
  (2, 1, '00000000-0000-0000-0000-000000000001', '2020-01-01 08:00+00', '2020-01-01 09:00+00', 150);

select setval(pg_get_serial_sequence('public.bikes', 'id'), 3);
select setval(pg_get_serial_sequence('public.rentals', 'id'), 2);
