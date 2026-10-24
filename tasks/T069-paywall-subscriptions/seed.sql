insert into auth.users (id, email) values
  ('00000000-0000-0000-0000-000000000001', 'ana@example.com'),
  ('00000000-0000-0000-0000-000000000002', 'ben@example.com'),
  ('00000000-0000-0000-0000-000000000003', 'cy@example.com'),
  ('00000000-0000-0000-0000-000000000004', 'dee@example.com'),
  ('00000000-0000-0000-0000-000000000005', 'eve@example.com');

insert into public.articles (id, title, body, is_premium) values
  (1, 'Monsoon travel tips', '...', false),
  (2, 'Deep dive: Indian equities', '...', true),
  (3, 'Exclusive interview', '...', true),
  (4, 'Weekly roundup', '...', false);

insert into public.subscriptions (user_id, plan, current_period_end) values
  ('00000000-0000-0000-0000-000000000001', 'pro', '2099-01-01'),
  ('00000000-0000-0000-0000-000000000002', 'pro', '2020-01-01'),
  ('00000000-0000-0000-0000-000000000003', 'free', '2099-01-01');
