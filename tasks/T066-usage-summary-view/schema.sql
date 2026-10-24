create table public.api_usage (
  user_id uuid not null references auth.users(id),
  day date not null,
  requests integer not null check (requests >= 0),
  primary key (user_id, day)
);
