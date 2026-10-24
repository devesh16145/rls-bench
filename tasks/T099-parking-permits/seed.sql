insert into auth.users (id, email) values
  ('00000000-0000-0000-0000-000000000001', 'ana@example.com'),
  ('00000000-0000-0000-0000-000000000002', 'ben@example.com'),
  ('00000000-0000-0000-0000-000000000003', 'hal@example.com');

insert into public.residents (unit_id, user_id) values (101, '00000000-0000-0000-0000-000000000001'), (102, '00000000-0000-0000-0000-000000000002');

insert into public.hoa_admins (user_id) values ('00000000-0000-0000-0000-000000000003');

insert into public.permits (id, unit_id, plate, valid_until, revoked) values
  (1, 101, 'MH12AB1234', '2099-01-01', false),
  (2, 101, 'MH12CD5678', '2099-01-01', false),
  (3, 102, 'MH14EF1111', '2020-06-30', false),
  (4, 102, 'MH14GH2222', '2099-01-01', true);

select setval(pg_get_serial_sequence('public.permits', 'id'), 4);
