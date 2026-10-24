insert into auth.users (id, email) values
  ('00000000-0000-0000-0000-000000000001', 'ana@example.com'),
  ('00000000-0000-0000-0000-000000000002', 'ben@example.com'),
  ('00000000-0000-0000-0000-000000000003', 'cy@example.com');

insert into public.recipes (id, author_id, title, is_public) values
  (1, '00000000-0000-0000-0000-000000000001', 'Dal tadka', true),
  (2, '00000000-0000-0000-0000-000000000001', 'Grandma''s secret chutney', false),
  (3, '00000000-0000-0000-0000-000000000002', 'Kanda poha', true);

insert into public.favorites (user_id, recipe_id) values ('00000000-0000-0000-0000-000000000002', 1), ('00000000-0000-0000-0000-000000000001', 3);

select setval(pg_get_serial_sequence('public.recipes', 'id'), 3);
