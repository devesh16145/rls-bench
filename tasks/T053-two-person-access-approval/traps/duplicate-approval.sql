create schema private;

grant usage on schema private to authenticated;

create function private.is_ops() returns boolean
language sql stable security definer set search_path = ''
as $$
  select exists (select 1 from public.ops_team o where o.user_id = auth.uid())
$$;

alter table public.ops_team enable row level security;
alter table public.access_requests enable row level security;
alter table public.access_approvals enable row level security;

create policy ops_team_select on public.ops_team
  for select to authenticated
  using (true);

create policy requests_select on public.access_requests
  for select to authenticated
  using (requester_id = auth.uid() or private.is_ops());

create policy requests_insert on public.access_requests
  for insert to authenticated
  with check (requester_id = auth.uid() and status = 'pending');

create policy requests_delete on public.access_requests
  for delete to authenticated
  using (requester_id = auth.uid() and status = 'pending');

create policy approvals_select on public.access_approvals
  for select to authenticated
  using (
    private.is_ops()
    or exists (select 1 from public.access_requests r where r.id = request_id and r.requester_id = auth.uid())
  );

create function public.approve_access(p_request_id bigint) returns text
language plpgsql security definer set search_path = ''
as $$
declare
  v_uid uuid := auth.uid();
  v_request public.access_requests%rowtype;
  v_approvers integer;
begin
  if v_uid is null or not exists (select 1 from public.ops_team o where o.user_id = v_uid) then
    raise exception 'only ops team members can approve';
  end if;
  select * into v_request from public.access_requests where id = p_request_id for update;
  if not found then
    raise exception 'unknown request';
  end if;
  if v_request.status <> 'pending' then
    raise exception 'request is not pending';
  end if;
  if v_request.requester_id = v_uid then
    raise exception 'cannot approve your own request';
  end if;
  insert into public.access_approvals (request_id, approver_id) values (p_request_id, v_uid);
  select count(distinct a.approver_id) into v_approvers from public.access_approvals a where a.request_id = p_request_id;
  if v_approvers >= 2 then
    update public.access_requests set status = 'granted' where id = p_request_id;
    return 'granted';
  end if;
  return 'pending';
end
$$;
