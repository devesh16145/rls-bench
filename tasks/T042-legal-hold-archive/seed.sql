insert into auth.users (id, email) values
  ('00000000-0000-0000-0000-000000000001', 'ana@example.com'),
  ('00000000-0000-0000-0000-000000000002', 'ben@example.com'),
  ('00000000-0000-0000-0000-000000000003', 'adm@example.com');

insert into public.org_admins (user_id) values ('00000000-0000-0000-0000-000000000003');

insert into public.files (id, owner_id, name, legal_hold) values
  (1, '00000000-0000-0000-0000-000000000001', 'q3-forecast.xlsx', false),
  (2, '00000000-0000-0000-0000-000000000001', 'vendor-dispute-emails.pdf', true),
  (3, '00000000-0000-0000-0000-000000000002', 'offsite-photos.zip', false);

select setval(pg_get_serial_sequence('public.files', 'id'), 3);
