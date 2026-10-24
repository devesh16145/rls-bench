create table public.app_config (
  key text primary key,
  value jsonb not null,
  is_public boolean not null default false,
  user_overridable boolean not null default false
);

create table public.user_flag_overrides (
  user_id uuid not null default auth.uid() references auth.users(id),
  key text not null references public.app_config(key),
  value jsonb not null,
  primary key (user_id, key)
);
