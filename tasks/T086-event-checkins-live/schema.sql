create table public.events (
  id bigint primary key,
  name text not null,
  starts_at timestamptz not null,
  ends_at timestamptz not null
);

create table public.checkins (
  event_id bigint not null references public.events(id),
  user_id uuid not null default auth.uid() references auth.users(id),
  checked_in_at timestamptz not null default now(),
  primary key (event_id, user_id)
);
