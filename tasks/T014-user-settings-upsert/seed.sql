insert into auth.users (id, email) values
  ('00000000-0000-0000-0000-000000000001', 'ana@example.com'),
  ('00000000-0000-0000-0000-000000000002', 'ben@example.com'),
  ('00000000-0000-0000-0000-000000000003', 'cy@example.com');

insert into public.user_settings (user_id, timezone, weekly_goal, reminders_enabled) values
  ('00000000-0000-0000-0000-000000000001', 'Europe/Lisbon', 5, true),
  ('00000000-0000-0000-0000-000000000002', 'Asia/Kolkata', 3, false);
