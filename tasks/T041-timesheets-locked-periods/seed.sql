insert into auth.users (id, email) values
  ('00000000-0000-0000-0000-000000000001', 'ana@example.com'),
  ('00000000-0000-0000-0000-000000000002', 'ben@example.com');

insert into public.projects (id, name) values (1, 'Website'), (2, 'Mobile app'), (3, 'Internal R&D');

insert into public.assignments (project_id, user_id) values (1, '00000000-0000-0000-0000-000000000001'), (2, '00000000-0000-0000-0000-000000000001'), (2, '00000000-0000-0000-0000-000000000002');

insert into public.periods (id, starts_on, ends_on, is_locked) values
  (1, '2020-01-01', '2020-01-31', true),
  (2, '2030-01-01', '2030-01-31', false);

insert into public.time_entries (id, user_id, project_id, period_id, worked_on, hours, note) values
  (1, '00000000-0000-0000-0000-000000000001', 1, 1, '2020-01-15', 8, 'Homepage'),
  (2, '00000000-0000-0000-0000-000000000001', 2, 2, '2030-01-10', 6, 'Login screen'),
  (3, '00000000-0000-0000-0000-000000000002', 2, 2, '2030-01-11', 7, 'API');

select setval(pg_get_serial_sequence('public.time_entries', 'id'), 3);
