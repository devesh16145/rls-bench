create schema private;

grant usage on schema private to authenticated;

create function private.is_finder(p_item_id bigint) returns boolean
language sql stable security definer set search_path = ''
as $$
  select exists (select 1 from public.items i where i.id = p_item_id and i.found_by = auth.uid())
$$;

create function private.item_open(p_item_id bigint) returns boolean
language sql stable security definer set search_path = ''
as $$
  select coalesce((select i.status = 'open' from public.items i where i.id = p_item_id), false)
$$;

create function private.other_approved(p_item_id bigint, p_claim_id bigint) returns boolean
language sql stable security definer set search_path = ''
as $$
  select exists (select 1 from public.claims c where c.item_id = p_item_id and c.id <> p_claim_id and c.status = 'approved')
$$;

alter table public.items enable row level security;
alter table public.claims enable row level security;

revoke update on public.claims from anon, authenticated;
grant update (status) on public.claims to authenticated;

create policy items_select on public.items
  for select to authenticated
  using (true);

create policy items_insert on public.items
  for insert to authenticated
  with check (found_by = auth.uid() and status = 'open');

create policy items_update on public.items
  for update to authenticated
  using (found_by = auth.uid())
  with check (found_by = auth.uid());

create policy claims_select on public.claims
  for select to authenticated
  using (claimant_id = auth.uid() or private.is_finder(item_id));

create policy claims_insert on public.claims
  for insert to authenticated
  with check (
    claimant_id = auth.uid()
    and status = 'pending'
    and not private.is_finder(item_id)
  );

create policy claims_update on public.claims
  for update to authenticated
  using (private.is_finder(item_id) and status = 'pending')
  with check (
    private.is_finder(item_id)
    and (status <> 'approved' or not private.other_approved(item_id, id))
  );
