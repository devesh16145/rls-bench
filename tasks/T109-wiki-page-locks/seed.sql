insert into auth.users (id, email) values
  ('00000000-0000-0000-0000-000000000001', 'm1@example.com'),
  ('00000000-0000-0000-0000-000000000002', 'm2@example.com'),
  ('00000000-0000-0000-0000-000000000003', 'outsider@example.com');

insert into public.spaces (id, name) values (1, 'Engineering'), (2, 'Design');

insert into public.members (space_id, user_id) values (1, '00000000-0000-0000-0000-000000000001'), (1, '00000000-0000-0000-0000-000000000002'), (2, '00000000-0000-0000-0000-000000000002');

insert into public.pages (id, space_id, title, body, locked_by, locked_until) values
  (1, 1, 'Onboarding', 'Welcome', null, null),
  (2, 1, 'Deploy runbook', 'Step 1', '00000000-0000-0000-0000-000000000002', '2099-01-01 00:00+00'),
  (3, 1, 'Incident template', 'Summary', '00000000-0000-0000-0000-000000000002', '2020-01-01 00:00+00'),
  (4, 2, 'Brand colours', '#2a78d6', null, null);

select setval(pg_get_serial_sequence('public.spaces', 'id'), 2);
select setval(pg_get_serial_sequence('public.pages', 'id'), 4);
