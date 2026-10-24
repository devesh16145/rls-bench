insert into auth.users (id, email) values
  ('00000000-0000-0000-0000-000000000001', 'ana@example.com'),
  ('00000000-0000-0000-0000-000000000002', 'ben@example.com');

insert into storage.buckets (id, name, public) values ('avatars', 'avatars', true), ('docs', 'docs', false);

insert into storage.objects (bucket_id, name, owner) values
  ('avatars', '00000000-0000-0000-0000-000000000001.png', '00000000-0000-0000-0000-000000000001'),
  ('avatars', '00000000-0000-0000-0000-000000000002.jpg', '00000000-0000-0000-0000-000000000002'),
  ('docs', 'secret.pdf', null);
