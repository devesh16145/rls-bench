alter table public.api_usage enable row level security;

create policy api_usage_select on public.api_usage
  for select to authenticated
  using (user_id = auth.uid());

create view public.usage_summary as
  select user_id, sum(requests)::bigint as total_requests, count(*)::bigint as active_days
  from public.api_usage
  group by user_id;
