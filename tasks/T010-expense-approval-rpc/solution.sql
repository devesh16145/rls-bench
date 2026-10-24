create schema private;

grant usage on schema private to authenticated;

create function private.is_department_member(p_department_id bigint) returns boolean
language sql stable security definer set search_path = ''
as $$
  select exists (
    select 1 from public.department_members m
    where m.department_id = p_department_id and m.user_id = auth.uid()
  )
$$;

create function private.is_department_manager(p_department_id bigint) returns boolean
language sql stable security definer set search_path = ''
as $$
  select exists (
    select 1 from public.department_members m
    where m.department_id = p_department_id and m.user_id = auth.uid() and m.is_manager
  )
$$;

alter table public.departments enable row level security;
alter table public.department_members enable row level security;
alter table public.expenses enable row level security;

revoke update on public.expenses from anon, authenticated;
grant update (amount) on public.expenses to authenticated;

create policy department_members_select on public.department_members
  for select to authenticated
  using (user_id = auth.uid());

create policy expenses_select on public.expenses
  for select to authenticated
  using (submitted_by = auth.uid() or private.is_department_manager(department_id));

create policy expenses_insert on public.expenses
  for insert to authenticated
  with check (
    submitted_by = auth.uid()
    and private.is_department_member(department_id)
    and status = 'pending'
    and decided_by is null
  );

create policy expenses_update on public.expenses
  for update to authenticated
  using (submitted_by = auth.uid() and status = 'pending')
  with check (submitted_by = auth.uid() and status = 'pending');

create function public.decide_expense(p_expense_id bigint, p_approve boolean) returns void
language plpgsql security definer set search_path = ''
as $$
declare
  v_expense public.expenses%rowtype;
begin
  select * into v_expense from public.expenses where id = p_expense_id for update;
  if not found or v_expense.status <> 'pending' then
    raise exception 'expense % is not pending', p_expense_id;
  end if;
  if auth.role() is distinct from 'service_role' then
    if auth.uid() is null
       or v_expense.submitted_by = auth.uid()
       or not exists (
         select 1 from public.department_members m
         where m.department_id = v_expense.department_id
           and m.user_id = auth.uid()
           and m.is_manager
       ) then
      raise exception 'not allowed to decide expense %', p_expense_id;
    end if;
  end if;
  update public.expenses
  set status = case when p_approve then 'approved' else 'rejected' end,
      decided_by = auth.uid()
  where id = p_expense_id;
end
$$;
