insert into auth.users (id, email) values
  ('00000000-0000-0000-0000-000000000001', 'ana@example.com'),
  ('00000000-0000-0000-0000-000000000002', 'ben@example.com');

insert into public.events (id, name, starts_at, ends_at) values
  (1, 'Always-on conference', '2020-01-01', '2099-01-01'),
  (2, 'Launch party', '2020-01-01', '2020-01-02'),
  (3, 'Future summit', '2099-01-01', '2099-01-02');

insert into public.checkins (event_id, user_id, checked_in_at) values (2, '00000000-0000-0000-0000-000000000001', '2020-01-01 19:00+00');
