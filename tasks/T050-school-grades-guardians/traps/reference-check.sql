create schema private;

grant usage on schema private to authenticated;

create function private.teaches(p_class_id bigint) returns boolean
language sql stable security definer set search_path = ''
as $$
  select exists (select 1 from public.classes c where c.id = p_class_id and c.teacher_id = auth.uid())
$$;

create function private.is_enrolled(p_class_id bigint, p_student_id uuid) returns boolean
language sql stable security definer set search_path = ''
as $$
  select exists (select 1 from public.class_students s where s.class_id = p_class_id and s.student_id = p_student_id)
$$;

create function private.guards(p_student_id uuid) returns boolean
language sql stable security definer set search_path = ''
as $$
  select exists (select 1 from public.guardians g where g.student_id = p_student_id and g.guardian_id = auth.uid())
$$;

alter table public.classes enable row level security;
alter table public.class_students enable row level security;
alter table public.guardians enable row level security;
alter table public.grades enable row level security;

create policy classes_select on public.classes
  for select to authenticated
  using (true);

create policy class_students_select on public.class_students
  for select to authenticated
  using (student_id = auth.uid() or private.teaches(class_id));

create policy guardians_select on public.guardians
  for select to authenticated
  using (guardian_id = auth.uid() or student_id = auth.uid());

create policy grades_select on public.grades
  for select to authenticated
  using (student_id = auth.uid() or private.guards(student_id) or private.teaches(class_id));

create policy grades_insert on public.grades
  for insert to authenticated
  with check (graded_by = auth.uid() and private.teaches(class_id));

create policy grades_update on public.grades
  for update to authenticated
  using (private.teaches(class_id))
  with check (graded_by = auth.uid() and private.teaches(class_id) and private.is_enrolled(class_id, student_id));

create policy grades_delete on public.grades
  for delete to authenticated
  using (private.teaches(class_id));
