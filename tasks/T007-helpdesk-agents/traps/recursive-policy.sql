create schema private;

grant usage on schema private to authenticated;

create function private.is_agent() returns boolean
language sql stable security definer set search_path = ''
as $$
  select coalesce(
    (select p.is_agent from public.profiles p where p.id = auth.uid()),
    false
  )
$$;

alter table public.profiles enable row level security;
alter table public.tickets enable row level security;

revoke update on public.profiles from anon, authenticated;
grant update (display_name) on public.profiles to authenticated;

create policy profiles_select on public.profiles
  for select to authenticated
  using (
    id = auth.uid()
    or exists (select 1 from public.profiles me where me.id = auth.uid() and me.is_agent)
  );

create policy profiles_update on public.profiles
  for update to authenticated
  using (id = auth.uid())
  with check (id = auth.uid());

create policy tickets_select on public.tickets
  for select to authenticated
  using (requester_id = auth.uid() or private.is_agent());

create policy tickets_insert on public.tickets
  for insert to authenticated
  with check (
    requester_id = auth.uid()
    and status = 'open'
    and assigned_agent is null
  );

create policy tickets_update on public.tickets
  for update to authenticated
  using (private.is_agent())
  with check (private.is_agent());
