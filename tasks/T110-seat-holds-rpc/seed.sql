insert into auth.users (id, email) values
  ('00000000-0000-0000-0000-000000000001', 'u1@example.com'),
  ('00000000-0000-0000-0000-000000000002', 'u2@example.com');

insert into public.events (id, name) values (1, 'Spring recital');

insert into public.seats (id, event_id, label, status, holder_id, hold_until, booked_by) values
  (1, 1, 'A1', 'free', null, null, null),
  (2, 1, 'A2', 'held', '00000000-0000-0000-0000-000000000002', '2099-01-01 00:00+00', null),
  (3, 1, 'A3', 'held', '00000000-0000-0000-0000-000000000002', '2020-01-01 00:00+00', null),
  (4, 1, 'A4', 'booked', null, null, '00000000-0000-0000-0000-000000000002'),
  (5, 1, 'A5', 'free', null, null, null),
  (6, 1, 'A6', 'held', '00000000-0000-0000-0000-000000000001', '2020-01-01 00:00+00', null);

select setval(pg_get_serial_sequence('public.events', 'id'), 1);
select setval(pg_get_serial_sequence('public.seats', 'id'), 6);
