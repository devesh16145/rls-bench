create table public.desks (
  id bigint primary key,
  label text not null,
  zone text not null check (zone in ('standard', 'premium'))
);

create table public.memberships (
  user_id uuid primary key references auth.users(id),
  tier text not null check (tier in ('standard', 'premium')),
  valid_until date not null
);

create table public.bookings (
  desk_id bigint not null references public.desks(id),
  day date not null,
  user_id uuid not null default auth.uid() references auth.users(id),
  primary key (desk_id, day)
);
