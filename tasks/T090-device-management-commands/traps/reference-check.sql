create schema private;

grant usage on schema private to authenticated;

create function private.is_org_admin(p_org_id bigint) returns boolean
language sql stable security definer set search_path = ''
as $$
  select exists (select 1 from public.org_admins a where a.org_id = p_org_id and a.user_id = auth.uid())
$$;

create function private.device_org(p_device_id bigint) returns bigint
language sql stable security definer set search_path = ''
as $$
  select d.org_id from public.devices d where d.id = p_device_id
$$;

create function private.assigned_to_me(p_device_id bigint) returns boolean
language sql stable security definer set search_path = ''
as $$
  select exists (select 1 from public.devices d where d.id = p_device_id and d.assigned_to = auth.uid())
$$;

create function private.is_any_admin() returns boolean
language sql stable security definer set search_path = ''
as $$
  select exists (select 1 from public.org_admins a where a.user_id = auth.uid())
$$;

alter table public.org_admins enable row level security;
alter table public.devices enable row level security;
alter table public.device_commands enable row level security;

create policy devices_select on public.devices
  for select to authenticated
  using (assigned_to = auth.uid() or private.is_org_admin(org_id));

create policy commands_select on public.device_commands
  for select to authenticated
  using (private.assigned_to_me(device_id) or private.is_org_admin(private.device_org(device_id)));

create policy commands_insert on public.device_commands
  for insert to authenticated
  with check (
    issued_by = auth.uid()
    and (
      private.is_any_admin()
      or (private.assigned_to_me(device_id) and command in ('locate', 'lock'))
    )
  );
