insert into auth.users (id, email) values
  ('00000000-0000-0000-0000-000000000001', 'ana@example.com'),
  ('00000000-0000-0000-0000-000000000002', 'ben@example.com'),
  ('00000000-0000-0000-0000-000000000003', 'cy@example.com'),
  ('00000000-0000-0000-0000-000000000004', 'lib@example.com');

insert into public.librarians (user_id) values ('00000000-0000-0000-0000-000000000004');

insert into public.books (id, title, copies) values
  (1, 'Dune', 1),
  (2, 'Emma', 2),
  (3, 'Ulysses', 3),
  (4, 'Beloved', 1),
  (5, 'Middlemarch', 2);

insert into public.loans (id, book_id, borrower_id, borrowed_on, returned_on) values
  (1, 1, '00000000-0000-0000-0000-000000000001', '2020-01-02', null),
  (2, 3, '00000000-0000-0000-0000-000000000001', '2020-01-03', null),
  (3, 2, '00000000-0000-0000-0000-000000000002', '2020-01-04', null),
  (4, 3, '00000000-0000-0000-0000-000000000002', '2020-01-05', null),
  (5, 5, '00000000-0000-0000-0000-000000000002', '2020-01-06', null),
  (6, 4, '00000000-0000-0000-0000-000000000003', '2020-01-01', '2020-01-10');

select setval(pg_get_serial_sequence('public.loans', 'id'), 6);
