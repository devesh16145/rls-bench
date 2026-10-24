insert into auth.users (id, email) values
  ('00000000-0000-0000-0000-000000000001', 'ana@example.com'),
  ('00000000-0000-0000-0000-000000000002', 'ben@example.com');

insert into public.app_config (key, value, is_public, user_overridable) values
  ('theme', '"light"', true, true),
  ('beta_editor', 'false', true, true),
  ('max_upload_mb', '25', true, false),
  ('stripe_webhook_secret', '"whsec_test_123"', false, false);

insert into public.user_flag_overrides (user_id, key, value) values
  ('00000000-0000-0000-0000-000000000001', 'theme', '"dark"');
