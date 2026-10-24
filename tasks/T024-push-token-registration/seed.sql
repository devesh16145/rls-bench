insert into auth.users (id, email) values
  ('00000000-0000-0000-0000-000000000001', 'ana@example.com'),
  ('00000000-0000-0000-0000-000000000002', 'ben@example.com'),
  ('00000000-0000-0000-0000-000000000003', 'cy@example.com');

insert into public.push_tokens (token, user_id, platform) values
  ('tok-ana-phone', '00000000-0000-0000-0000-000000000001', 'ios'),
  ('tok-ben-web', '00000000-0000-0000-0000-000000000002', 'web');
