insert into auth.users (id, email) values
  ('00000000-0000-0000-0000-000000000001', 'ana@example.com'),
  ('00000000-0000-0000-0000-000000000002', 'ben@example.com');

insert into public.decks (id, owner_id, name, is_public) values
  (1, '00000000-0000-0000-0000-000000000001', 'Hindi basics', true),
  (2, '00000000-0000-0000-0000-000000000001', 'Exam cram', false),
  (3, '00000000-0000-0000-0000-000000000002', 'Tamil phrases', true);

insert into public.cards (id, deck_id, front, back) values
  (1, 1, 'namaste', 'hello'),
  (2, 1, 'dhanyavaad', 'thank you'),
  (3, 2, 'mitochondria', 'powerhouse of the cell'),
  (4, 3, 'vanakkam', 'hello');

select setval(pg_get_serial_sequence('public.cards', 'id'), 4);
