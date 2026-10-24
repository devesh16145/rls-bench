create table public.locations (
  id bigint primary key,
  name text not null,
  is_frozen boolean not null default false
);

create table public.location_staff (
  location_id bigint not null references public.locations(id),
  user_id uuid not null references auth.users(id),
  primary key (location_id, user_id)
);

create table public.stock (
  location_id bigint not null references public.locations(id),
  sku text not null,
  qty integer not null check (qty >= 0),
  primary key (location_id, sku)
);
