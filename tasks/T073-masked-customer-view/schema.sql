create table public.support_agents (
  user_id uuid primary key references auth.users(id),
  region text not null
);

create table public.supervisors (
  user_id uuid primary key references auth.users(id)
);

create table public.customers (
  id bigint primary key,
  region text not null,
  full_name text not null,
  email text not null,
  phone text not null
);
