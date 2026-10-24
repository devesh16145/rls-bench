alter table public.courses enable row level security;
alter table public.lessons enable row level security;
alter table public.enrollments enable row level security;

create policy courses_select on public.courses
  for select to anon, authenticated
  using (is_published or instructor_id = auth.uid());

create policy courses_insert on public.courses
  for insert to authenticated
  with check (instructor_id = auth.uid());

create policy courses_update on public.courses
  for update to authenticated
  using (instructor_id = auth.uid())
  with check (instructor_id = auth.uid());

create policy courses_delete on public.courses
  for delete to authenticated
  using (instructor_id = auth.uid());

create policy lessons_select on public.lessons
  for select to anon, authenticated
  using (exists (
    select 1 from public.courses c
    where c.id = lessons.course_id
      and (
        c.instructor_id = auth.uid()
        or c.is_published
      )
  ));

create policy lessons_insert on public.lessons
  for insert to authenticated
  with check (exists (select 1 from public.courses c where c.id = course_id and c.instructor_id = auth.uid()));

create policy lessons_update on public.lessons
  for update to authenticated
  using (exists (select 1 from public.courses c where c.id = course_id and c.instructor_id = auth.uid()))
  with check (exists (select 1 from public.courses c where c.id = course_id and c.instructor_id = auth.uid()));

create policy lessons_delete on public.lessons
  for delete to authenticated
  using (exists (select 1 from public.courses c where c.id = course_id and c.instructor_id = auth.uid()));

create policy enrollments_select on public.enrollments
  for select to authenticated
  using (
    student_id = auth.uid()
    or exists (select 1 from public.courses c where c.id = course_id and c.instructor_id = auth.uid())
  );

create policy enrollments_insert on public.enrollments
  for insert to authenticated
  with check (
    student_id = auth.uid()
    and exists (select 1 from public.courses c where c.id = course_id and c.is_published)
  );

create policy enrollments_delete on public.enrollments
  for delete to authenticated
  using (student_id = auth.uid());
