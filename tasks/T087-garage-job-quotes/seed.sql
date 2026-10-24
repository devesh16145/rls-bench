insert into auth.users (id, email) values
  ('00000000-0000-0000-0000-000000000001', 'mo@example.com'),
  ('00000000-0000-0000-0000-000000000002', 'ned@example.com'),
  ('00000000-0000-0000-0000-000000000003', 'cal@example.com'),
  ('00000000-0000-0000-0000-000000000004', 'dee@example.com');

insert into public.garages (id, name) values (1, 'Speedy Motors'), (2, 'Ned''s Garage');

insert into public.mechanics (garage_id, user_id) values (1, '00000000-0000-0000-0000-000000000001'), (2, '00000000-0000-0000-0000-000000000002');

insert into public.jobs (id, garage_id, customer_id, vehicle, status, quote_amount) values
  (1, 1, '00000000-0000-0000-0000-000000000003', 'Swift 2018', 'quoted', 4500),
  (2, 1, '00000000-0000-0000-0000-000000000004', 'City 2016', 'approved', 3000),
  (3, 2, '00000000-0000-0000-0000-000000000003', 'Activa 2019', 'in_progress', 800);

select setval(pg_get_serial_sequence('public.jobs', 'id'), 3);
