create table public.events (
  id bigint primary key,
  host_id uuid not null references auth.users(id),
  title text not null,
  is_private boolean not null default false,
  capacity integer not null check (capacity > 0)
);

create table public.invites (
  event_id bigint not null references public.events(id) on delete cascade,
  user_id uuid not null references auth.users(id),
  primary key (event_id, user_id)
);

create table public.rsvps (
  event_id bigint not null references public.events(id) on delete cascade,
  user_id uuid not null references auth.users(id),
  created_at timestamptz not null default '2020-01-01',
  primary key (event_id, user_id)
);
