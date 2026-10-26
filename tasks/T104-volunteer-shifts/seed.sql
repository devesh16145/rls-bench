insert into auth.users (id, email) values
  ('00000000-0000-0000-0000-000000000001', 'vol1@example.com'),
  ('00000000-0000-0000-0000-000000000002', 'vol2@example.com'),
  ('00000000-0000-0000-0000-000000000003', 'coord@example.com');

insert into public.coordinators (user_id) values ('00000000-0000-0000-0000-000000000003');

insert into public.shifts (id, title, starts_at, capacity, status, created_by) values
  (1, 'Saturday food bank', '2099-03-01 09:00+00', 2, 'open', '00000000-0000-0000-0000-000000000003'),
  (2, 'Sunday delivery run', '2099-03-02 09:00+00', 1, 'open', '00000000-0000-0000-0000-000000000003'),
  (3, 'Cancelled cleanup', '2099-03-03 09:00+00', 5, 'cancelled', '00000000-0000-0000-0000-000000000003'),
  (4, 'Past fundraiser', '2020-01-01 09:00+00', 5, 'open', '00000000-0000-0000-0000-000000000003');

insert into public.signups (id, shift_id, volunteer_id, status) values
  (1, 1, '00000000-0000-0000-0000-000000000002', 'active'),
  (2, 2, '00000000-0000-0000-0000-000000000001', 'active'),
  (3, 4, '00000000-0000-0000-0000-000000000001', 'cancelled');

select setval(pg_get_serial_sequence('public.shifts', 'id'), 4);
select setval(pg_get_serial_sequence('public.signups', 'id'), 3);
