insert into auth.users (id, email) values
  ('00000000-0000-0000-0000-000000000001', 'ana@example.com'),
  ('00000000-0000-0000-0000-000000000002', 'ben@example.com'),
  ('00000000-0000-0000-0000-000000000003', 'cy@example.com'),
  ('00000000-0000-0000-0000-000000000004', 'dee@example.com'),
  ('00000000-0000-0000-0000-000000000005', 'eli@example.com');

insert into public.profiles (user_id, display_name, bio, visibility) values
  ('00000000-0000-0000-0000-000000000001', 'Ana', 'Designer in Pune', 'public'),
  ('00000000-0000-0000-0000-000000000002', 'Ben', 'Backend dev', 'members'),
  ('00000000-0000-0000-0000-000000000003', 'Cy', 'Prefers privacy', 'private');
