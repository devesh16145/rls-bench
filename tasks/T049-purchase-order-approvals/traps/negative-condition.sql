create schema private;

grant usage on schema private to authenticated;

create function private.approver_limit() returns numeric
language sql stable security definer set search_path = ''
as $$
  select a.limit_amount from public.approvers a where a.user_id = auth.uid()
$$;

create function private.po_decided(p_po_id bigint) returns boolean
language sql stable security definer set search_path = ''
as $$
  select exists (select 1 from public.po_approvals d where d.po_id = p_po_id)
$$;

create function private.can_decide(p_po_id bigint) returns boolean
language sql stable security definer set search_path = ''
as $$
  select exists (
    select 1 from public.purchase_orders po
    where po.id = p_po_id
      and po.requester_id <> auth.uid()
      and po.amount <= coalesce((select a.limit_amount from public.approvers a where a.user_id = auth.uid()), -1)
  )
$$;

alter table public.approvers enable row level security;
alter table public.purchase_orders enable row level security;
alter table public.po_approvals enable row level security;

create policy approvers_select on public.approvers
  for select to authenticated
  using (user_id = auth.uid());

create policy po_select on public.purchase_orders
  for select to authenticated
  using (requester_id = auth.uid() or private.approver_limit() is not null);

create policy po_insert on public.purchase_orders
  for insert to authenticated
  with check (requester_id = auth.uid());

create policy po_update on public.purchase_orders
  for update to authenticated
  using (requester_id = auth.uid())
  with check (requester_id = auth.uid());

create policy po_delete on public.purchase_orders
  for delete to authenticated
  using (requester_id = auth.uid() and not private.po_decided(id));

create policy po_approvals_select on public.po_approvals
  for select to authenticated
  using (
    private.approver_limit() is not null
    or exists (select 1 from public.purchase_orders po where po.id = po_id and po.requester_id = auth.uid())
  );

create policy po_approvals_insert on public.po_approvals
  for insert to authenticated
  with check (approver_id = auth.uid() and private.can_decide(po_id));
