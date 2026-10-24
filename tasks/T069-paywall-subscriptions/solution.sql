create schema private;

grant usage on schema private to anon, authenticated;

create function private.has_pro() returns boolean
language sql stable security definer set search_path = ''
as $$
  select exists (select 1 from public.subscriptions s where s.user_id = auth.uid() and s.plan = 'pro' and s.current_period_end > now())
$$;

alter table public.articles enable row level security;
alter table public.subscriptions enable row level security;

create policy articles_select on public.articles
  for select to anon, authenticated
  using (not is_premium or private.has_pro());

create policy subscriptions_select on public.subscriptions
  for select to authenticated
  using (user_id = auth.uid());
