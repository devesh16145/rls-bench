create schema private;

grant usage on schema private to authenticated;

create function private.is_mechanic(p_garage_id bigint) returns boolean
language sql stable security definer set search_path = ''
as $$
  select exists (select 1 from public.mechanics m where m.garage_id = p_garage_id and m.user_id = auth.uid())
$$;

create function private.job_status(p_job_id bigint) returns text
language sql stable security definer set search_path = ''
as $$
  select j.status from public.jobs j where j.id = p_job_id
$$;

create function private.job_unchanged(p_job_id bigint, p_garage_id bigint, p_customer_id uuid, p_vehicle text, p_quote numeric) returns boolean
language sql stable security definer set search_path = ''
as $$
  select exists (
    select 1 from public.jobs j
    where j.id = p_job_id and j.garage_id = p_garage_id and j.customer_id = p_customer_id
      and j.vehicle = p_vehicle and j.quote_amount = p_quote
  )
$$;

alter table public.garages enable row level security;
alter table public.mechanics enable row level security;
alter table public.jobs enable row level security;

create policy garages_select on public.garages
  for select to authenticated
  using (true);

create policy jobs_select on public.jobs
  for select to authenticated
  using (customer_id = auth.uid() or private.is_mechanic(garage_id));

create policy jobs_insert on public.jobs
  for insert to authenticated
  with check (private.is_mechanic(garage_id) and status = 'quoted');

create policy jobs_mechanic_update on public.jobs
  for update to authenticated
  using (private.is_mechanic(garage_id))
  with check (
    private.is_mechanic(garage_id)
    and (
      (private.job_status(id) = 'quoted' and status = 'quoted')
      or (
        private.job_status(id) in ('approved', 'in_progress')
        and status in ('in_progress', 'done')
        and private.job_unchanged(id, garage_id, customer_id, vehicle, quote_amount)
      )
    )
  );

create policy jobs_customer_update on public.jobs
  for update to authenticated
  using (customer_id = auth.uid() and status = 'quoted')
  with check (
    customer_id = auth.uid()
    and status = 'approved'
    and private.job_unchanged(id, garage_id, customer_id, vehicle, quote_amount)
  );
