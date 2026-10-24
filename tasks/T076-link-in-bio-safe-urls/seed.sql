insert into auth.users (id, email) values
  ('00000000-0000-0000-0000-000000000001', 'ana@example.com'),
  ('00000000-0000-0000-0000-000000000002', 'ben@example.com');

insert into public.bio_links (id, user_id, title, url, position, is_visible) values
  (1, '00000000-0000-0000-0000-000000000001', 'Portfolio', 'https://ana.example.com', 1, true),
  (2, '00000000-0000-0000-0000-000000000001', 'Draft shop', 'https://shop.example.com', 2, false),
  (3, '00000000-0000-0000-0000-000000000002', 'Podcast', 'https://ben.example.com/pod', 1, true);

select setval(pg_get_serial_sequence('public.bio_links', 'id'), 3);
