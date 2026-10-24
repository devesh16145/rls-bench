create schema private;

grant usage on schema private to anon, authenticated;

create function private.is_employee() returns boolean
language sql stable security definer set search_path = ''
as $$
  select exists (select 1 from public.employees e where e.user_id = auth.uid())
$$;

create function private.is_hr() returns boolean
language sql stable security definer set search_path = ''
as $$
  select exists (select 1 from public.employees e where e.user_id = auth.uid() and e.department = 'HR')
$$;

alter table public.employees enable row level security;

create policy employees_select on public.employees
  for select to authenticated
  using (user_id = auth.uid() or private.is_hr());

create policy employees_update on public.employees
  for update to authenticated
  using (private.is_hr())
  with check (private.is_hr());

create view public.employee_directory as
  select id, full_name, department
  from public.employees;
