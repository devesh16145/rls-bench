create table public.profiles (
  id uuid primary key references auth.users(id),
  username text not null unique,
  bio text,
  avatar_url text
);
