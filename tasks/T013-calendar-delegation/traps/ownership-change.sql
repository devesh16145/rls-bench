create schema private;

grant usage on schema private to anon, authenticated;

create function private.has_delegation(p_grantor_id uuid, p_edit boolean) returns boolean
language sql stable security definer set search_path = ''
as $$
  select exists (
    select 1 from public.delegations d
    where d.grantor_id = p_grantor_id
      and d.delegate_id = auth.uid()
      and (d.expires_at is null or d.expires_at > now())
      and (d.can_edit or not p_edit)
  )
$$;

create function private.event_owner(p_event_id bigint) returns uuid
language sql stable security definer set search_path = ''
as $$
  select e.owner_id from public.events e where e.id = p_event_id
$$;

alter table public.events enable row level security;
alter table public.delegations enable row level security;

create policy events_select on public.events
  for select to authenticated
  using (owner_id = auth.uid() or (not is_private and private.has_delegation(owner_id, false)));

create policy events_insert on public.events
  for insert to authenticated
  with check (owner_id = auth.uid() or (not is_private and private.has_delegation(owner_id, true)));

create policy events_update on public.events
  for update to authenticated
  using (owner_id = auth.uid() or (not is_private and private.has_delegation(owner_id, true)))
  with check (
    (owner_id = auth.uid() or (not is_private and private.has_delegation(owner_id, true)))
  );

create policy events_delete on public.events
  for delete to authenticated
  using (owner_id = auth.uid() or (not is_private and private.has_delegation(owner_id, true)));

create policy delegations_select on public.delegations
  for select to authenticated
  using (grantor_id = auth.uid() or delegate_id = auth.uid());

create policy delegations_insert on public.delegations
  for insert to authenticated
  with check (grantor_id = auth.uid());

create policy delegations_update on public.delegations
  for update to authenticated
  using (grantor_id = auth.uid())
  with check (grantor_id = auth.uid());

create policy delegations_delete on public.delegations
  for delete to authenticated
  using (grantor_id = auth.uid());

create view public.busy_slots as
  select e.owner_id, e.starts_at, e.ends_at
  from public.events e
  where e.owner_id = auth.uid()
     or private.has_delegation(e.owner_id, false)
     or auth.role() = 'service_role';
