create schema private;

grant usage on schema private to authenticated;

create function private.teaches_folder(p_folder text) returns boolean
language sql stable security definer set search_path = ''
as $$
  select exists (select 1 from public.courses c where c.id::text = p_folder and c.instructor_id = auth.uid())
$$;

create function private.enrolled_in_folder(p_folder text) returns boolean
language sql stable security definer set search_path = ''
as $$
  select exists (select 1 from public.enrollments e join public.courses c on c.id = e.course_id where c.id::text = p_folder and e.student_id = auth.uid())
$$;

alter table public.courses enable row level security;
alter table public.enrollments enable row level security;

create policy courses_select on public.courses
  for select to authenticated
  using (true);

create policy enrollments_select on public.enrollments
  for select to authenticated
  using (student_id = auth.uid());

create policy materials_select on storage.objects
  for select to authenticated
  using (
    bucket_id = 'materials'
    and (private.teaches_folder((storage.foldername(name))[1]) or private.enrolled_in_folder((storage.foldername(name))[1]))
  );

create policy materials_insert on storage.objects
  for insert to authenticated
  with check (
    bucket_id = 'materials'
    and private.teaches_folder((storage.foldername(name))[1])
    and owner = auth.uid()
  );

create policy materials_update on storage.objects
  for update to authenticated
  using (bucket_id = 'materials' and private.teaches_folder((storage.foldername(name))[1]))
  with check (
    bucket_id = 'materials'
    and private.teaches_folder((storage.foldername(name))[1])
    and owner = auth.uid()
    and (name like '%.pdf' or name like '%.mp4')
  );

create policy materials_delete on storage.objects
  for delete to authenticated
  using (bucket_id = 'materials' and private.teaches_folder((storage.foldername(name))[1]));
