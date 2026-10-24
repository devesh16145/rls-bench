insert into auth.users (id, email) values
  ('00000000-0000-0000-0000-000000000001', 'ana@example.com'),
  ('00000000-0000-0000-0000-000000000002', 'ben@example.com');

insert into public.board_notes (id, author_id, body, color, is_pinned) values
  (1, '00000000-0000-0000-0000-000000000001', 'Office closed on Friday', 'red', true),
  (2, '00000000-0000-0000-0000-000000000002', 'Lost: blue water bottle', 'blue', false);

select setval(pg_get_serial_sequence('public.board_notes', 'id'), 2);
