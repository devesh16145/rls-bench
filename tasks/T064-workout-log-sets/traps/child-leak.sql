alter table public.workouts enable row level security;
alter table public.workout_sets enable row level security;

create policy workouts_select on public.workouts
  for select to authenticated
  using (user_id = auth.uid());

create policy workouts_insert on public.workouts
  for insert to authenticated
  with check (user_id = auth.uid());

create policy workouts_update on public.workouts
  for update to authenticated
  using (user_id = auth.uid())
  with check (user_id = auth.uid());

create policy workouts_delete on public.workouts
  for delete to authenticated
  using (user_id = auth.uid());

create policy workout_sets_select on public.workout_sets
  for select to authenticated
  using (true);

create policy workout_sets_insert on public.workout_sets
  for insert to authenticated
  with check (exists (select 1 from public.workouts w where w.id = workout_id and w.user_id = auth.uid()));

create policy workout_sets_update on public.workout_sets
  for update to authenticated
  using (exists (select 1 from public.workouts w where w.id = workout_id and w.user_id = auth.uid()))
  with check (exists (select 1 from public.workouts w where w.id = workout_id and w.user_id = auth.uid()));

create policy workout_sets_delete on public.workout_sets
  for delete to authenticated
  using (exists (select 1 from public.workouts w where w.id = workout_id and w.user_id = auth.uid()));
