create table public.providers (
  user_id uuid primary key references auth.users(id),
  name text not null
);

create table public.slots (
  id bigint primary key,
  provider_id uuid not null references public.providers(user_id),
  starts_at timestamptz not null,
  booked_by uuid references auth.users(id)
);
