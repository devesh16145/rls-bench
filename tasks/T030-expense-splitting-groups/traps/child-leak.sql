create schema private;

grant usage on schema private to authenticated;

create function private.is_member(p_group_id bigint) returns boolean
language sql stable security definer set search_path = ''
as $$
  select exists (select 1 from public.group_members m where m.group_id = p_group_id and m.user_id = auth.uid())
$$;

create function private.is_group_member(p_group_id bigint, p_user_id uuid) returns boolean
language sql stable security definer set search_path = ''
as $$
  select exists (select 1 from public.group_members m where m.group_id = p_group_id and m.user_id = p_user_id)
$$;

create function private.expense_group(p_expense_id bigint) returns bigint
language sql stable security definer set search_path = ''
as $$
  select e.group_id from public.expenses e where e.id = p_expense_id
$$;

create function private.expense_payer(p_expense_id bigint) returns uuid
language sql stable security definer set search_path = ''
as $$
  select e.paid_by from public.expenses e where e.id = p_expense_id
$$;

alter table public.groups enable row level security;
alter table public.group_members enable row level security;
alter table public.expenses enable row level security;
alter table public.expense_shares enable row level security;

create policy groups_select on public.groups
  for select to authenticated
  using (private.is_member(id));

create policy group_members_select on public.group_members
  for select to authenticated
  using (private.is_member(group_id));

create policy expenses_select on public.expenses
  for select to authenticated
  using (private.is_member(group_id));

create policy expenses_insert on public.expenses
  for insert to authenticated
  with check (paid_by = auth.uid() and private.is_member(group_id));

create policy expenses_update on public.expenses
  for update to authenticated
  using (paid_by = auth.uid())
  with check (paid_by = auth.uid() and group_id = private.expense_group(id));

create policy expenses_delete on public.expenses
  for delete to authenticated
  using (paid_by = auth.uid());

create policy expense_shares_select on public.expense_shares
  for select to authenticated
  using (true);

create policy expense_shares_insert on public.expense_shares
  for insert to authenticated
  with check (
    private.expense_payer(expense_id) = auth.uid()
    and private.is_group_member(private.expense_group(expense_id), user_id)
  );

create policy expense_shares_update on public.expense_shares
  for update to authenticated
  using (private.expense_payer(expense_id) = auth.uid())
  with check (
    private.expense_payer(expense_id) = auth.uid()
    and private.is_group_member(private.expense_group(expense_id), user_id)
  );

create policy expense_shares_delete on public.expense_shares
  for delete to authenticated
  using (private.expense_payer(expense_id) = auth.uid());
