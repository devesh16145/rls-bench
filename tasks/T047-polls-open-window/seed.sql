insert into auth.users (id, email) values
  ('00000000-0000-0000-0000-000000000001', 'ana@example.com'),
  ('00000000-0000-0000-0000-000000000002', 'ben@example.com'),
  ('00000000-0000-0000-0000-000000000003', 'cy@example.com');

insert into public.polls (id, question, closes_at) values
  (1, 'Where should the offsite be?', '2099-01-01'),
  (2, 'Pick the 2020 team colour', '2020-02-01');

insert into public.poll_options (id, poll_id, label) values
  (1, 1, 'Goa'), (2, 1, 'Coorg'), (3, 2, 'Teal'), (4, 2, 'Orange');

insert into public.votes (poll_id, user_id, option_id) values
  (1, '00000000-0000-0000-0000-000000000001', 1),
  (2, '00000000-0000-0000-0000-000000000002', 3);
