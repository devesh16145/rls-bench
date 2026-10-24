create schema private;

grant usage on schema private to authenticated;

create function private.is_member(p_org_id bigint) returns boolean
language sql stable security definer set search_path = ''
as $$
  select exists (select 1 from public.org_members m where m.org_id = p_org_id and m.user_id = auth.uid())
$$;

alter table public.org_members enable row level security;
alter table public.leaderboard enable row level security;

create policy org_members_select on public.org_members
  for select to authenticated
  using (private.is_member(org_id));

create policy leaderboard_select on public.leaderboard
  for select to authenticated
  using (true);

create function public.set_member_role(p_org_id bigint, p_user_id uuid, p_role text) returns text
language plpgsql security definer set search_path = ''
as $$
declare
  v_uid uuid := auth.uid();
  v_target_role text;
begin
  if p_user_id = v_uid then
    raise exception 'you cannot change your own role';
  end if;
  if p_role is null or p_role not in ('admin', 'member') then
    raise exception 'role must be admin or member';
  end if;
  select m.role into v_target_role from public.org_members m where m.org_id = p_org_id and m.user_id = p_user_id;
  if not found then
    raise exception 'not a member of this organization';
  end if;
  if v_target_role = 'owner' then
    raise exception 'owners cannot be changed';
  end if;
  update public.org_members set role = p_role where org_id = p_org_id and user_id = p_user_id;
  return p_role;
end
$$;

create function public.recalculate_leaderboard() returns void
language sql security definer set search_path = ''
as $$
  update public.leaderboard set score = greatest(score, 0);
$$;

revoke execute on function public.recalculate_leaderboard() from public, anon, authenticated;
grant execute on function public.recalculate_leaderboard() to service_role;
