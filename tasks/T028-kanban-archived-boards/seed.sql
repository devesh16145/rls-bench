insert into auth.users (id, email) values
  ('00000000-0000-0000-0000-000000000001', 'ana@example.com'),
  ('00000000-0000-0000-0000-000000000002', 'ben@example.com'),
  ('00000000-0000-0000-0000-000000000003', 'cy@example.com'),
  ('00000000-0000-0000-0000-000000000004', 'dee@example.com');

insert into public.boards (id, name, is_archived) values
  (1, 'Launch', false),
  (2, 'Q1 2020', true);

insert into public.board_members (board_id, user_id, role) values
  (1, '00000000-0000-0000-0000-000000000001', 'editor'),
  (1, '00000000-0000-0000-0000-000000000002', 'viewer'),
  (2, '00000000-0000-0000-0000-000000000001', 'viewer'),
  (2, '00000000-0000-0000-0000-000000000003', 'editor');

insert into public.cards (id, board_id, title, column_name, assignee_id) values
  (1, 1, 'Write copy', 'todo', '00000000-0000-0000-0000-000000000002'),
  (2, 1, 'Design hero', 'doing', null),
  (3, 2, 'Old task', 'done', null);

select setval(pg_get_serial_sequence('public.cards', 'id'), 3);
