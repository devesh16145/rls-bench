insert into auth.users (id, email) values
  ('00000000-0000-0000-0000-000000000001', 'ana@example.com'),
  ('00000000-0000-0000-0000-000000000002', 'ben@example.com');

insert into public.journal_entries (id, user_id, body, mood, created_at) values
  (1, '00000000-0000-0000-0000-000000000001', 'First entry', 3, '2020-01-01'),
  (2, '00000000-0000-0000-0000-000000000002', 'Ben entry', 5, '2020-01-02');

select setval(pg_get_serial_sequence('public.journal_entries', 'id'), 2);
