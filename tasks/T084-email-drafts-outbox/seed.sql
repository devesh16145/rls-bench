insert into auth.users (id, email) values
  ('00000000-0000-0000-0000-000000000001', 'ana@example.com'),
  ('00000000-0000-0000-0000-000000000002', 'ben@example.com');

insert into public.emails (id, user_id, to_address, subject, body, sent_at) values
  (1, '00000000-0000-0000-0000-000000000001', 'raj@example.org', 'Lunch?', 'Free on Friday?', null),
  (2, '00000000-0000-0000-0000-000000000001', 'hr@example.org', 'Leave request', 'Taking Monday off.', '2020-01-05'),
  (3, '00000000-0000-0000-0000-000000000002', 'ops@example.org', 'Server down', 'Please check.', null);

select setval(pg_get_serial_sequence('public.emails', 'id'), 3);
