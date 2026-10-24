create schema private;

grant usage on schema private to authenticated;

create function private.course_role(p_course_id bigint) returns text
language sql stable security definer set search_path = ''
as $$
  select e.role from public.enrollments e where e.course_id = p_course_id and e.user_id = auth.uid()
$$;

create function private.thread_course(p_thread_id bigint) returns bigint
language sql stable security definer set search_path = ''
as $$
  select t.course_id from public.threads t where t.id = p_thread_id
$$;

create function private.thread_locked(p_thread_id bigint) returns boolean
language sql stable security definer set search_path = ''
as $$
  select coalesce((select t.is_locked from public.threads t where t.id = p_thread_id), true)
$$;

alter table public.courses enable row level security;
alter table public.enrollments enable row level security;
alter table public.threads enable row level security;
alter table public.posts enable row level security;

create policy courses_select on public.courses
  for select to authenticated
  using (private.course_role(id) is not null);

create policy enrollments_select on public.enrollments
  for select to authenticated
  using (user_id = auth.uid());

create policy threads_select on public.threads
  for select to authenticated
  using (private.course_role(course_id) is not null);

create policy threads_insert on public.threads
  for insert to authenticated
  with check (created_by = auth.uid() and not is_locked and private.course_role(course_id) is not null);

create policy threads_update on public.threads
  for update to authenticated
  using (private.course_role(course_id) = 'ta')
  with check (private.course_role(course_id) = 'ta');

create policy posts_select on public.posts
  for select to authenticated
  using (private.course_role(private.thread_course(thread_id)) is not null);

create policy posts_insert on public.posts
  for insert to authenticated
  with check (
    author_id = auth.uid()
    and private.course_role(private.thread_course(thread_id)) is not null
    and not private.thread_locked(thread_id)
  );

create policy posts_update on public.posts
  for update to authenticated
  using (author_id = auth.uid() and not private.thread_locked(thread_id))
  with check (
    author_id = auth.uid()
    and private.course_role(private.thread_course(thread_id)) is not null
    and not private.thread_locked(thread_id)
  );

create policy posts_delete on public.posts
  for delete to authenticated
  using (
    (author_id = auth.uid() and not private.thread_locked(thread_id))
    or private.course_role(private.thread_course(thread_id)) = 'ta'
  );
