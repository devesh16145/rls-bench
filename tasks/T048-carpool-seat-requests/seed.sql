insert into auth.users (id, email) values
  ('00000000-0000-0000-0000-000000000001', 'dev@example.com'),
  ('00000000-0000-0000-0000-000000000002', 'pia@example.com'),
  ('00000000-0000-0000-0000-000000000003', 'quinn@example.com'),
  ('00000000-0000-0000-0000-000000000004', 'raj@example.com'),
  ('00000000-0000-0000-0000-000000000005', 'sana@example.com');

insert into public.rides (id, driver_id, from_city, to_city, departs_at, seats) values
  (1, '00000000-0000-0000-0000-000000000001', 'Pune', 'Mumbai', '2099-03-01 07:00+00', 2),
  (2, '00000000-0000-0000-0000-000000000001', 'Pune', 'Nashik', '2020-03-01 07:00+00', 3),
  (3, '00000000-0000-0000-0000-000000000005', 'Bengaluru', 'Mysuru', '2099-04-01 08:00+00', 1);

insert into public.ride_bookings (ride_id, passenger_id, status) values
  (1, '00000000-0000-0000-0000-000000000002', 'confirmed'),
  (1, '00000000-0000-0000-0000-000000000003', 'requested'),
  (3, '00000000-0000-0000-0000-000000000004', 'confirmed'),
  (3, '00000000-0000-0000-0000-000000000003', 'requested');
