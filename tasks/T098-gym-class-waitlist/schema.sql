create table public.classes (
  id bigint primary key,
  title text not null,
  capacity integer not null check (capacity > 0),
  instructor_id uuid not null references auth.users(id)
);

create table public.class_spots (
  class_id bigint not null references public.classes(id),
  user_id uuid not null default auth.uid() references auth.users(id),
  status text not null check (status in ('enrolled', 'waitlisted')),
  primary key (class_id, user_id)
);
