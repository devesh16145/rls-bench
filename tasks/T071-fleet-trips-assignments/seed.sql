insert into auth.users (id, email) values
  ('00000000-0000-0000-0000-000000000001', 'mo@example.com'),
  ('00000000-0000-0000-0000-000000000002', 'dia@example.com'),
  ('00000000-0000-0000-0000-000000000003', 'eli@example.com');

insert into public.fleet_managers (user_id) values ('00000000-0000-0000-0000-000000000001');

insert into public.vehicles (id, plate) values (1, 'MH12AB1234'), (2, 'MH12CD5678');

insert into public.assignments (id, vehicle_id, driver_id, starts_on, ends_on) values
  (1, 1, '00000000-0000-0000-0000-000000000002', '2020-01-01', '2020-01-31'),
  (2, 2, '00000000-0000-0000-0000-000000000003', '2020-01-01', '2020-12-31'),
  (3, 1, '00000000-0000-0000-0000-000000000003', '2020-02-01', '2020-02-29');

insert into public.trips (id, vehicle_id, driver_id, trip_date, km) values
  (1, 1, '00000000-0000-0000-0000-000000000002', '2020-01-10', 120),
  (2, 2, '00000000-0000-0000-0000-000000000003', '2020-03-01', 35);

select setval(pg_get_serial_sequence('public.assignments', 'id'), 3);
select setval(pg_get_serial_sequence('public.trips', 'id'), 2);
