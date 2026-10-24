insert into auth.users (id, email) values
  ('00000000-0000-0000-0000-000000000001', 'ana@example.com'),
  ('00000000-0000-0000-0000-000000000002', 'ben@example.com'),
  ('00000000-0000-0000-0000-000000000003', 'cy@example.com');

insert into public.household_members (household_id, user_id) values (1, '00000000-0000-0000-0000-000000000001'), (1, '00000000-0000-0000-0000-000000000002'), (2, '00000000-0000-0000-0000-000000000003');

insert into public.shopping_items (id, household_id, name, added_by, claimed_by, is_bought) values
  (1, 1, 'Milk', '00000000-0000-0000-0000-000000000001', null, false),
  (2, 1, 'Eggs', '00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000002', false),
  (3, 1, 'Rice', '00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000001', true),
  (4, 2, 'Tea', '00000000-0000-0000-0000-000000000003', null, false);

select setval(pg_get_serial_sequence('public.shopping_items', 'id'), 4);
