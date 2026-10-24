create table public.events (
  id bigint primary key,
  name text not null,
  deadline timestamptz not null
);

create table public.teams (
  id bigint primary key,
  event_id bigint not null references public.events(id),
  name text not null
);

create table public.team_members (
  team_id bigint not null references public.teams(id),
  user_id uuid not null references auth.users(id),
  primary key (team_id, user_id)
);

create table public.judges (
  event_id bigint not null references public.events(id),
  user_id uuid not null references auth.users(id),
  primary key (event_id, user_id)
);

create table public.submissions (
  team_id bigint primary key references public.teams(id),
  repo_url text not null,
  notes text,
  updated_at timestamptz not null default '2020-01-01'
);
