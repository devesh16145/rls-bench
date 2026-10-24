insert into auth.users (id, email) values
  ('00000000-0000-0000-0000-000000000001', 'ana@example.com'),
  ('00000000-0000-0000-0000-000000000002', 'ben@example.com'),
  ('00000000-0000-0000-0000-000000000003', 'cy@example.com');

insert into storage.buckets (id, name, public) values
  ('media', 'media', false),
  ('internal', 'internal', false);

insert into storage.objects (bucket_id, name, owner) values
  ('media', '00000000-0000-0000-0000-000000000001/public/cv.pdf', '00000000-0000-0000-0000-000000000001'),
  ('media', '00000000-0000-0000-0000-000000000001/private/passport.png', '00000000-0000-0000-0000-000000000001'),
  ('media', '00000000-0000-0000-0000-000000000002/public/logo.svg', '00000000-0000-0000-0000-000000000002'),
  ('media', '00000000-0000-0000-0000-000000000002/private/notes.txt', '00000000-0000-0000-0000-000000000002'),
  ('media', '00000000-0000-0000-0000-000000000003/private/public/x.txt', '00000000-0000-0000-0000-000000000003'),
  ('media', 'shared/readme.txt', null),
  ('internal', 'reports/q3.pdf', null);
