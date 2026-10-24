create table public.org_members (
  org_id bigint not null,
  user_id uuid not null references auth.users(id),
  role text not null check (role in ('owner', 'admin', 'member')),
  primary key (org_id, user_id)
);

create table public.leaderboard (
  user_id uuid primary key references auth.users(id),
  score integer not null
);
