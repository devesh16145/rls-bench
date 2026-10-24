create table public.polls (
  id bigint primary key,
  question text not null,
  closes_at timestamptz not null
);

create table public.poll_options (
  id bigint primary key,
  poll_id bigint not null references public.polls(id),
  label text not null
);

create table public.votes (
  poll_id bigint not null references public.polls(id),
  user_id uuid not null default auth.uid() references auth.users(id),
  option_id bigint not null references public.poll_options(id),
  primary key (poll_id, user_id)
);
