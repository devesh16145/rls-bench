create table public.courses (
  id bigint primary key,
  instructor_id uuid not null references auth.users(id),
  title text not null,
  is_published boolean not null default false
);

create table public.lessons (
  id bigint primary key,
  course_id bigint not null references public.courses(id) on delete cascade,
  title text not null,
  body text not null default '',
  is_preview boolean not null default false
);

create table public.enrollments (
  course_id bigint not null references public.courses(id) on delete cascade,
  student_id uuid not null references auth.users(id),
  primary key (course_id, student_id)
);
