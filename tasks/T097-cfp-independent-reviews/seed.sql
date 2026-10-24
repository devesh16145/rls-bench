insert into auth.users (id, email) values
  ('00000000-0000-0000-0000-000000000001', 'spk1@example.com'),
  ('00000000-0000-0000-0000-000000000002', 'spk2@example.com'),
  ('00000000-0000-0000-0000-000000000003', 'rv1@example.com'),
  ('00000000-0000-0000-0000-000000000004', 'rv2@example.com');

insert into public.reviewers (user_id) values ('00000000-0000-0000-0000-000000000003'), ('00000000-0000-0000-0000-000000000004');

insert into public.proposals (id, speaker_id, title, status) values
  (1, '00000000-0000-0000-0000-000000000001', 'Postgres RLS in practice', 'submitted'),
  (2, '00000000-0000-0000-0000-000000000002', 'Scaling with read replicas', 'accepted'),
  (3, '00000000-0000-0000-0000-000000000003', 'Testing policies', 'submitted');

insert into public.reviews (proposal_id, reviewer_id, score, comment) values
  (1, '00000000-0000-0000-0000-000000000004', 4, 'Solid'),
  (2, '00000000-0000-0000-0000-000000000003', 5, 'Great'),
  (2, '00000000-0000-0000-0000-000000000004', 3, 'Good');

select setval(pg_get_serial_sequence('public.proposals', 'id'), 3);
