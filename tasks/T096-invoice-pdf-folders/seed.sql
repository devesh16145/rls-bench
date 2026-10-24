insert into auth.users (id, email) values
  ('00000000-0000-0000-0000-000000000001', 'ana@example.com'),
  ('00000000-0000-0000-0000-000000000002', 'ben@example.com');

insert into storage.buckets (id, name, public) values ('invoices', 'invoices', false);

insert into storage.objects (bucket_id, name, owner) values
  ('invoices', '00000000-0000-0000-0000-000000000001/2020-01.pdf', '00000000-0000-0000-0000-000000000001'),
  ('invoices', '00000000-0000-0000-0000-000000000002/2020-01.pdf', '00000000-0000-0000-0000-000000000002'),
  ('invoices', 'misc/readme.txt', null);
