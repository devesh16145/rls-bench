insert into auth.users (id, email) values
  ('00000000-0000-0000-0000-000000000001', 'gia@example.com'),
  ('00000000-0000-0000-0000-000000000002', 'hugo@example.com'),
  ('00000000-0000-0000-0000-000000000003', 'sam@example.com'),
  ('00000000-0000-0000-0000-000000000004', 'tess@example.com');

insert into public.restaurants (id, name) values (1, 'Bombay Canteen'), (2, 'Masque');

insert into public.restaurant_staff (restaurant_id, user_id) values (1, '00000000-0000-0000-0000-000000000003'), (2, '00000000-0000-0000-0000-000000000004');

insert into public.reservations (id, restaurant_id, user_id, reserved_for, party_size, status) values
  (1, 1, '00000000-0000-0000-0000-000000000001', '2099-05-01 19:00+00', 2, 'booked'),
  (2, 1, '00000000-0000-0000-0000-000000000001', '2020-02-01 20:00+00', 4, 'booked'),
  (3, 1, '00000000-0000-0000-0000-000000000002', '2099-06-01 13:00+00', 3, 'booked'),
  (4, 2, '00000000-0000-0000-0000-000000000002', '2020-03-01 21:00+00', 2, 'booked');

select setval(pg_get_serial_sequence('public.reservations', 'id'), 4);
