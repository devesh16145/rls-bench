create schema private;

grant usage on schema private to authenticated;

create function private.household_role(p_household_id bigint) returns text
language sql stable security definer set search_path = ''
as $$
  select m.role from public.household_members m where m.household_id = p_household_id and m.user_id = auth.uid()
$$;

create function private.is_child_of(p_household_id bigint, p_user_id uuid) returns boolean
language sql stable security definer set search_path = ''
as $$
  select exists (select 1 from public.household_members m where m.household_id = p_household_id and m.user_id = p_user_id and m.role = 'child')
$$;

create function private.chore_unchanged(p_id bigint, p_household_id bigint, p_title text, p_assignee uuid, p_points integer) returns boolean
language sql stable security definer set search_path = ''
as $$
  select exists (
    select 1 from public.chores c
    where c.id = p_id and c.household_id = p_household_id and c.title = p_title
      and c.assignee_id = p_assignee and c.points = p_points
  )
$$;

alter table public.households enable row level security;
alter table public.household_members enable row level security;
alter table public.chores enable row level security;

create policy households_select on public.households
  for select to authenticated
  using (private.household_role(id) is not null);

create policy household_members_select on public.household_members
  for select to authenticated
  using (private.household_role(household_id) is not null);

create policy chores_select on public.chores
  for select to authenticated
  using (private.household_role(household_id) is not null);

create policy chores_insert on public.chores
  for insert to authenticated
  with check (
    private.household_role(household_id) = 'parent'
    and private.is_child_of(household_id, assignee_id)
    and status = 'todo'
  );

create policy chores_parent_update on public.chores
  for update to authenticated
  using (private.household_role(household_id) = 'parent' and status <> 'approved')
  with check (private.household_role(household_id) = 'parent' and private.is_child_of(household_id, assignee_id));

create policy chores_child_update on public.chores
  for update to authenticated
  using (assignee_id = auth.uid() and status = 'todo')
  with check (
    assignee_id = auth.uid()
    and status = 'done'
  );

create policy chores_delete on public.chores
  for delete to authenticated
  using (private.household_role(household_id) = 'parent' and status <> 'approved');
