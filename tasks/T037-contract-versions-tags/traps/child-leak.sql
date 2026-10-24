create schema private;

grant usage on schema private to authenticated;

create function private.is_contract_owner(p_contract_id bigint) returns boolean
language sql stable security definer set search_path = ''
as $$
  select exists (select 1 from public.contracts c where c.id = p_contract_id and c.owner_id = auth.uid())
$$;

create function private.can_read_contract(p_contract_id bigint) returns boolean
language sql stable security definer set search_path = ''
as $$
  select exists (
    select 1 from public.contracts c
    where c.id = p_contract_id
      and (c.owner_id = auth.uid()
           or exists (select 1 from public.contract_shares s where s.contract_id = c.id and s.user_id = auth.uid()))
  )
$$;

alter table public.contracts enable row level security;
alter table public.contract_shares enable row level security;
alter table public.contract_versions enable row level security;
alter table public.contract_tags enable row level security;

create policy contracts_select on public.contracts
  for select to authenticated
  using (
    owner_id = auth.uid()
    or exists (select 1 from public.contract_shares s where s.contract_id = contracts.id and s.user_id = auth.uid())
  );

create policy contracts_insert on public.contracts
  for insert to authenticated
  with check (owner_id = auth.uid());

create policy contracts_update on public.contracts
  for update to authenticated
  using (owner_id = auth.uid())
  with check (owner_id = auth.uid());

create policy contracts_delete on public.contracts
  for delete to authenticated
  using (owner_id = auth.uid());

create policy contract_shares_select on public.contract_shares
  for select to authenticated
  using (user_id = auth.uid() or private.is_contract_owner(contract_id));

create policy contract_shares_insert on public.contract_shares
  for insert to authenticated
  with check (private.is_contract_owner(contract_id));

create policy contract_shares_delete on public.contract_shares
  for delete to authenticated
  using (private.is_contract_owner(contract_id));

create policy contract_versions_select on public.contract_versions
  for select to authenticated
  using (true);

create policy contract_versions_insert on public.contract_versions
  for insert to authenticated
  with check (created_by = auth.uid() and private.can_read_contract(contract_id));

create policy contract_tags_select on public.contract_tags
  for select to authenticated
  using (private.can_read_contract(contract_id));

create policy contract_tags_insert on public.contract_tags
  for insert to authenticated
  with check (private.is_contract_owner(contract_id));

create policy contract_tags_delete on public.contract_tags
  for delete to authenticated
  using (private.is_contract_owner(contract_id));
