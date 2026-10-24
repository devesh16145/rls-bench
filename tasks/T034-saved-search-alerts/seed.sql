insert into auth.users (id, email) values
  ('00000000-0000-0000-0000-000000000001', 'ana@example.com'),
  ('00000000-0000-0000-0000-000000000002', 'ben@example.com');

insert into public.saved_searches (id, user_id, query, notify_email, frequency) values
  (1, '00000000-0000-0000-0000-000000000001', '2BHK in Pune under 40k', 'ana@example.com', 'weekly'),
  (2, '00000000-0000-0000-0000-000000000002', 'Studio near Goa beach', null, 'off');

select setval(pg_get_serial_sequence('public.saved_searches', 'id'), 2);
