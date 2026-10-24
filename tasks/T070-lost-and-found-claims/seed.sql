insert into auth.users (id, email) values
  ('00000000-0000-0000-0000-000000000001', 'fay@example.com'),
  ('00000000-0000-0000-0000-000000000002', 'gil@example.com'),
  ('00000000-0000-0000-0000-000000000003', 'hal@example.com'),
  ('00000000-0000-0000-0000-000000000004', 'ivy@example.com'),
  ('00000000-0000-0000-0000-000000000005', 'jo@example.com');

insert into public.items (id, found_by, description, status) values
  (1, '00000000-0000-0000-0000-000000000001', 'Blue notebook at the library', 'open'),
  (2, '00000000-0000-0000-0000-000000000001', 'Umbrella at the bus stop', 'claimed');

insert into public.claims (id, item_id, claimant_id, message, status) values
  (1, 1, '00000000-0000-0000-0000-000000000002', 'My name is on page 1', 'pending'),
  (2, 1, '00000000-0000-0000-0000-000000000003', 'I lost one like it', 'pending'),
  (3, 2, '00000000-0000-0000-0000-000000000004', 'Black with a wooden handle', 'approved'),
  (4, 2, '00000000-0000-0000-0000-000000000003', 'Could be mine', 'pending');

select setval(pg_get_serial_sequence('public.items', 'id'), 2);
select setval(pg_get_serial_sequence('public.claims', 'id'), 4);
