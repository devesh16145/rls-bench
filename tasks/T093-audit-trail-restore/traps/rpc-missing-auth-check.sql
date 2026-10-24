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

create function private.record_org(p_record_id bigint) returns bigint
language sql stable security definer set search_path = ''
as $$
  select r.org_id from public.records r where r.id = p_record_id
$$;

create function private.audit_records() returns trigger
language plpgsql security definer set search_path = ''
as $$
begin
  insert into public.audit_log (record_id, action, actor) values (new.id, lower(tg_op), auth.uid());
  return new;
end
$$;

create trigger records_audit
  after insert or update on public.records
  for each row execute function private.audit_records();

alter table public.org_members enable row level security;
alter table public.records enable row level security;
alter table public.audit_log enable row level security;

create policy org_members_select on public.org_members
  for select to authenticated
  using (user_id = auth.uid());

create policy records_select on public.records
  for select to authenticated
  using (private.is_member(org_id) and (deleted_at is null or private.is_admin(org_id)));

create policy records_insert on public.records
  for insert to authenticated
  with check (private.is_member(org_id) and deleted_at is null);

create policy records_update on public.records
  for update to authenticated
  using (private.is_member(org_id) and (deleted_at is null or private.is_admin(org_id)))
  with check (private.is_member(org_id) and (deleted_at is null or private.is_admin(org_id)));

create policy audit_log_select on public.audit_log
  for select to authenticated
  using (private.is_admin(private.record_org(record_id)));

create function public.restore_record(p_record_id bigint) returns void
language plpgsql security definer set search_path = ''
as $$
declare
  v_record public.records%rowtype;
begin
  select * into v_record from public.records where id = p_record_id for update;
  if not found then
    raise exception 'unknown record';
  end if;
  if v_record.deleted_at is null then
    raise exception 'record is not deleted';
  end if;
  if v_record.deleted_at < now() - interval '30 days' then
    raise exception 'record was deleted more than 30 days ago';
  end if;
  update public.records set deleted_at = null where id = p_record_id;
end
$$;
