create schema private;

grant usage on schema private to authenticated;

create function private.is_finance() returns boolean
language sql stable security definer set search_path = ''
as $$
  select exists (select 1 from public.employees e where e.user_id = auth.uid() and e.is_finance)
$$;

create function private.manager_of(p_employee_id uuid) returns uuid
language sql stable security definer set search_path = ''
as $$
  select e.manager_id from public.employees e where e.user_id = p_employee_id
$$;

alter table public.employees enable row level security;
alter table public.adjustments enable row level security;

revoke update on public.adjustments from anon, authenticated;
grant update (status, approved_by) on public.adjustments to authenticated;

create policy employees_select on public.employees
  for select to authenticated
  using (user_id = auth.uid() or manager_id = auth.uid() or private.is_finance());

create policy adjustments_select on public.adjustments
  for select to authenticated
  using (employee_id = auth.uid() or private.manager_of(employee_id) = auth.uid() or private.is_finance());

create policy adjustments_insert on public.adjustments
  for insert to authenticated
  with check (
    status = 'pending' and approved_by is null and created_by = auth.uid()
    and employee_id <> auth.uid()
    and (private.is_finance() or private.manager_of(employee_id) = auth.uid())
  );

create policy adjustments_update on public.adjustments
  for update to authenticated
  using (
    status = 'pending'
    and (private.is_finance() or private.manager_of(employee_id) = auth.uid())
  )
  with check (
    status in ('approved', 'rejected')
    and approved_by = auth.uid()
    and employee_id <> auth.uid()
    and (
      private.is_finance()
      or private.manager_of(employee_id) = auth.uid()
    )
  );
