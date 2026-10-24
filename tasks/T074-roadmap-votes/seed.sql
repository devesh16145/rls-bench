insert into auth.users (id, email) values
  ('00000000-0000-0000-0000-000000000001', 'ana@example.com'),
  ('00000000-0000-0000-0000-000000000002', 'ben@example.com');

insert into public.roadmap_items (id, title, status) values
  (1, 'Dark mode', 'planned'),
  (2, 'Offline sync', 'in_progress'),
  (3, 'CSV export', 'shipped');

insert into public.item_votes (user_id, item_id) values ('00000000-0000-0000-0000-000000000001', 1), ('00000000-0000-0000-0000-000000000002', 1), ('00000000-0000-0000-0000-000000000002', 3);
