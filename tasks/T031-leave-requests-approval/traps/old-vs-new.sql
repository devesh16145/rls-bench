create schema private;

grant usage on schema private to authenticated;

create function private.is_manager_of(p_employee_id uuid) returns boolean
language sql stable security definer set search_path = ''
as $$
  select exists (
    select 1 from public.employees e
    where e.user_id = p_employee_id and e.manager_id = auth.uid()
  )
$$;

create function private.leave_guard() returns trigger
language plpgsql security definer set search_path = ''
as $$
begin
  if auth.role() = 'service_role' then
    return new;
  end if;
  if old.status <> 'pending' then
    raise exception 'request % is closed', old.id;
  end if;
  if new.employee_id is distinct from old.employee_id then
    raise exception 'employee cannot change';
  end if;
  if old.employee_id = auth.uid() then
    if new.status not in ('pending', 'cancelled') or new.decided_by is not null then
      raise exception 'employees cannot decide their own requests';
    end if;
    return new;
  end if;
  if private.is_manager_of(old.employee_id) then
    if new.status not in ('approved', 'rejected') or new.decided_by is distinct from auth.uid() then
      raise exception 'managers can only approve or reject, as themselves';
    end if;
    return new;
  end if;
  raise exception 'not allowed';
end
$$;

create trigger leave_requests_guard
  before update on public.leave_requests
  for each row execute function private.leave_guard();

alter table public.employees enable row level security;
alter table public.leave_requests enable row level security;

create policy employees_select on public.employees
  for select to authenticated
  using (true);

create policy leave_select on public.leave_requests
  for select to authenticated
  using (employee_id = auth.uid() or private.is_manager_of(employee_id));

create policy leave_insert on public.leave_requests
  for insert to authenticated
  with check (employee_id = auth.uid() and status = 'pending' and decided_by is null);

create policy leave_update on public.leave_requests
  for update to authenticated
  using (status = 'pending' and (employee_id = auth.uid() or private.is_manager_of(employee_id)))
  with check (employee_id = auth.uid() or private.is_manager_of(employee_id));
