create table public.push_tokens (
  token text primary key,
  user_id uuid not null default auth.uid() references auth.users(id),
  platform text not null check (platform in ('ios', 'android', 'web')),
  updated_at timestamptz not null default '2020-01-01'
);
