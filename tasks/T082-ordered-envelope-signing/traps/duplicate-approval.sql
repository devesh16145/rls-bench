create schema private;

grant usage on schema private to authenticated;

create function private.on_envelope(p_envelope_id bigint) returns boolean
language sql stable security definer set search_path = ''
as $$
  select exists (select 1 from public.envelopes e where e.id = p_envelope_id and e.sender_id = auth.uid())
    or exists (select 1 from public.envelope_recipients r where r.envelope_id = p_envelope_id and r.user_id = auth.uid())
$$;

alter table public.envelopes enable row level security;
alter table public.envelope_recipients enable row level security;

create policy envelopes_select on public.envelopes
  for select to authenticated
  using (private.on_envelope(id));

create policy recipients_select on public.envelope_recipients
  for select to authenticated
  using (private.on_envelope(envelope_id));

create function public.sign_envelope(p_envelope_id bigint) returns text
language plpgsql security definer set search_path = ''
as $$
declare
  v_uid uuid := auth.uid();
  v_recipient public.envelope_recipients%rowtype;
  v_status text;
begin
  select status into v_status from public.envelopes where id = p_envelope_id for update;
  if not found then
    raise exception 'unknown envelope';
  end if;
  select * into v_recipient from public.envelope_recipients
  where envelope_id = p_envelope_id and user_id = v_uid;
  if v_uid is null or not found then
    raise exception 'not a recipient';
  end if;
  if v_status <> 'sent' then
    raise exception 'envelope is %', v_status;
  end if;
  if exists (
    select 1 from public.envelope_recipients r
    where r.envelope_id = p_envelope_id and r.sign_order < v_recipient.sign_order and r.signed_at is null
  ) then
    raise exception 'earlier recipients have not signed yet';
  end if;
  update public.envelope_recipients set signed_at = now()
  where envelope_id = p_envelope_id and user_id = v_uid;
  if not exists (select 1 from public.envelope_recipients r where r.envelope_id = p_envelope_id and r.signed_at is null) then
    update public.envelopes set status = 'completed' where id = p_envelope_id;
    return 'completed';
  end if;
  return 'sent';
end
$$;

create function public.void_envelope(p_envelope_id bigint) returns text
language plpgsql security definer set search_path = ''
as $$
begin
  update public.envelopes set status = 'voided'
  where id = p_envelope_id and sender_id = auth.uid() and status = 'sent';
  if not found then
    raise exception 'cannot void this envelope';
  end if;
  return 'voided';
end
$$;
