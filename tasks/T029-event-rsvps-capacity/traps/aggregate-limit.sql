create schema private;

grant usage on schema private to authenticated;

create function private.is_host(p_event_id bigint) returns boolean
language sql stable security definer set search_path = ''
as $$
  select exists (select 1 from public.events e where e.id = p_event_id and e.host_id = auth.uid())
$$;

create function private.can_see_event(p_event_id bigint) returns boolean
language sql stable security definer set search_path = ''
as $$
  select exists (
    select 1 from public.events e
    where e.id = p_event_id
      and (not e.is_private or e.host_id = auth.uid()
           or exists (select 1 from public.invites i where i.event_id = e.id and i.user_id = auth.uid()))
  )
$$;

create function private.seats_left(p_event_id bigint) returns integer
language sql stable security definer set search_path = ''
as $$
  select e.capacity - (select count(*)::integer from public.rsvps r where r.event_id = e.id) from public.events e where e.id = p_event_id
$$;

create function private.has_rsvp(p_event_id bigint) returns boolean
language sql stable security definer set search_path = ''
as $$
  select exists (select 1 from public.rsvps r where r.event_id = p_event_id and r.user_id = auth.uid())
$$;

alter table public.events enable row level security;
alter table public.invites enable row level security;
alter table public.rsvps enable row level security;

create policy events_select on public.events
  for select to authenticated
  using (
    not is_private
    or host_id = auth.uid()
    or exists (select 1 from public.invites i where i.event_id = events.id and i.user_id = auth.uid())
  );

create policy events_insert on public.events
  for insert to authenticated
  with check (host_id = auth.uid());

create policy events_update on public.events
  for update to authenticated
  using (host_id = auth.uid())
  with check (host_id = auth.uid());

create policy events_delete on public.events
  for delete to authenticated
  using (host_id = auth.uid());

create policy invites_select on public.invites
  for select to authenticated
  using (user_id = auth.uid() or private.is_host(event_id));

create policy invites_insert on public.invites
  for insert to authenticated
  with check (private.is_host(event_id));

create policy invites_delete on public.invites
  for delete to authenticated
  using (private.is_host(event_id));

create policy rsvps_select on public.rsvps
  for select to authenticated
  using (user_id = auth.uid() or private.is_host(event_id) or private.has_rsvp(event_id));

create policy rsvps_insert on public.rsvps
  for insert to authenticated
  with check (
    user_id = auth.uid()
    and private.can_see_event(event_id)
  );

create policy rsvps_delete on public.rsvps
  for delete to authenticated
  using (user_id = auth.uid());
