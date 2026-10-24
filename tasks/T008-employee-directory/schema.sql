create table public.employees (
  id bigint primary key,
  user_id uuid not null unique references auth.users(id),
  full_name text not null,
  department text not null,
  salary numeric(12, 2) not null
);
