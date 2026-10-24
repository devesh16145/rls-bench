insert into auth.users (id, email) values
  ('00000000-0000-0000-0000-000000000001', 'ana@example.com'),
  ('00000000-0000-0000-0000-000000000002', 'ben@example.com');

insert into public.workouts (id, user_id, performed_on, kind) values
  (1, '00000000-0000-0000-0000-000000000001', '2020-01-06', 'strength'),
  (2, '00000000-0000-0000-0000-000000000002', '2020-01-07', 'strength');

insert into public.workout_sets (id, workout_id, exercise, reps, weight_kg) values
  (1, 1, 'Squat', 5, 80),
  (2, 1, 'Bench press', 5, 55),
  (3, 2, 'Deadlift', 3, 120);

select setval(pg_get_serial_sequence('public.workouts', 'id'), 2);
select setval(pg_get_serial_sequence('public.workout_sets', 'id'), 3);
