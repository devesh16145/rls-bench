create schema private;

grant usage on schema private to authenticated;

create function private.is_supervisor() returns boolean
language sql stable security definer set search_path = ''
as $$
  select exists (select 1 from public.supervisors s where s.user_id = auth.uid())
$$;

alter table public.support_agents enable row level security;
alter table public.supervisors enable row level security;
alter table public.customers enable row level security;

create policy support_agents_select on public.support_agents
  for select to authenticated
  using (user_id = auth.uid());

create policy supervisors_select on public.supervisors
  for select to authenticated
  using (user_id = auth.uid());

create policy customers_select on public.customers
  for select to authenticated
  using (private.is_supervisor());

create view public.support_customers as
  select
    c.id,
    c.region,
    c.full_name,
    left(c.email, 1) || '***' || substr(c.email, strpos(c.email, '@')) as email_masked,
    '******' || right(c.phone, 4) as phone_masked
  from public.customers c
  where c.region = coalesce(auth.jwt() -> 'user_metadata' ->> 'region', (select a.region from public.support_agents a where a.user_id = auth.uid()))
     or auth.role() = 'service_role';
