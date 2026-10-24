create schema private;

grant usage on schema private to authenticated;

create function private.is_member(p_household_id bigint) returns boolean
language sql stable security definer set search_path = ''
as $$
  select exists (select 1 from public.household_members m where m.household_id = p_household_id and m.user_id = auth.uid())
$$;

alter table public.household_members enable row level security;
alter table public.shopping_items enable row level security;

revoke update on public.shopping_items from anon, authenticated;
grant update (claimed_by, is_bought) on public.shopping_items to authenticated;

create policy household_members_select on public.household_members
  for select to authenticated
  using (private.is_member(household_id));

create policy items_select on public.shopping_items
  for select to authenticated
  using (private.is_member(household_id));

create policy items_insert on public.shopping_items
  for insert to authenticated
  with check (added_by = auth.uid() and claimed_by is null and not is_bought);

create policy items_update on public.shopping_items
  for update to authenticated
  using (private.is_member(household_id) and (claimed_by is null or claimed_by = auth.uid()))
  with check (
    private.is_member(household_id)
    and (claimed_by is null or claimed_by = auth.uid())
    and (not is_bought or claimed_by = auth.uid())
  );

create policy items_delete on public.shopping_items
  for delete to authenticated
  using (added_by = auth.uid() and not is_bought and private.is_member(household_id));
