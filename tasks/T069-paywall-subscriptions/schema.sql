create table public.articles (
  id bigint primary key,
  title text not null,
  body text not null,
  is_premium boolean not null default false
);

create table public.subscriptions (
  user_id uuid primary key references auth.users(id),
  plan text not null check (plan in ('free', 'pro')),
  current_period_end timestamptz not null
);
