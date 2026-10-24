create schema private;

grant usage on schema private to authenticated;

create function private.is_member(p_org_id bigint) returns boolean
language sql stable security definer set search_path = ''
as $$
  select exists (select 1 from public.org_members m where m.org_id = p_org_id and m.user_id = auth.uid())
$$;

create function private.is_admin(p_org_id bigint) returns boolean
language sql stable security definer set search_path = ''
as $$
  select exists (select 1 from public.org_members m where m.org_id = p_org_id and m.user_id = auth.uid() and m.role = 'admin')
$$;

alter table public.orgs enable row level security;
alter table public.org_members enable row level security;
alter table public.invites enable row level security;

create policy orgs_select on public.orgs
  for select to authenticated
  using (private.is_member(id));

create policy org_members_select on public.org_members
  for select to authenticated
  using (private.is_member(org_id));

create policy invites_select on public.invites
  for select to authenticated
  using (true);

create policy invites_insert on public.invites
  for insert to authenticated
  with check (
    private.is_admin(org_id)
    and invited_by = auth.uid()
    and accepted_at is null
    and expires_at > now()
  );

create policy invites_delete on public.invites
  for delete to authenticated
  using (private.is_admin(org_id));

create function public.accept_invite(p_token text) returns bigint
language plpgsql security definer set search_path = ''
as $$
declare
  v_invite public.invites%rowtype;
  v_uid uuid := auth.uid();
  v_email text := lower(auth.jwt() ->> 'email');
begin
  if v_uid is null then
    raise exception 'not signed in';
  end if;
  select * into v_invite from public.invites where token = p_token for update;
  if not found then
    raise exception 'invalid invite';
  end if;
  if v_invite.accepted_at is not null then
    raise exception 'invite already used';
  end if;
  if v_invite.expires_at <= now() then
    raise exception 'invite expired';
  end if;
  if v_email is null or lower(v_invite.email) <> v_email then
    raise exception 'invite is for a different email address';
  end if;
  insert into public.org_members (org_id, user_id, role)
  values (v_invite.org_id, v_uid, v_invite.role);
  update public.invites set accepted_at = now() where token = p_token;
  return v_invite.org_id;
end
$$;
