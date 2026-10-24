create table public.rides (
  id bigint primary key,
  driver_id uuid not null references auth.users(id),
  from_city text not null,
  to_city text not null,
  departs_at timestamptz not null,
  seats integer not null check (seats > 0)
);

create table public.ride_bookings (
  ride_id bigint not null references public.rides(id) on delete cascade,
  passenger_id uuid not null default auth.uid() references auth.users(id),
  status text not null default 'requested' check (status in ('requested', 'confirmed', 'declined')),
  primary key (ride_id, passenger_id)
);
