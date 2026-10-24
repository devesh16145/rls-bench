create schema private;

grant usage on schema private to authenticated;

create function private.is_clinician() returns boolean
language sql stable security definer set search_path = ''
as $$
  select exists (select 1 from public.clinicians c where c.user_id = auth.uid())
$$;

create function private.is_auditor() returns boolean
language sql stable security definer set search_path = ''
as $$
  select exists (select 1 from public.auditors a where a.user_id = auth.uid())
$$;

create function private.can_read_patient(p_patient_id bigint) returns boolean
language sql stable security definer set search_path = ''
as $$
  select exists (select 1 from public.care_team t where t.patient_id = p_patient_id and t.clinician_id = auth.uid())
    or exists (
      select 1 from public.break_glass_grants g
      where g.patient_id = p_patient_id and g.clinician_id = auth.uid() and g.expires_at > now()
    )
$$;

alter table public.clinicians enable row level security;
alter table public.auditors enable row level security;
alter table public.care_team enable row level security;
alter table public.medical_records enable row level security;
alter table public.break_glass_grants enable row level security;

create policy medical_records_select on public.medical_records
  for select to authenticated
  using (private.can_read_patient(patient_id));

create policy grants_select on public.break_glass_grants
  for select to authenticated
  using (clinician_id = auth.uid() or private.is_auditor());

create function public.break_glass(p_patient_id bigint, p_reason text) returns timestamptz
language plpgsql security definer set search_path = ''
as $$
declare
  v_uid uuid := auth.uid();
  v_expires timestamptz := now() + interval '1 hour';
begin
  if v_uid is null or not exists (select 1 from public.clinicians c where c.user_id = v_uid) then
    raise exception 'only clinicians can break the glass';
  end if;
  if not exists (select 1 from public.patients p where p.id = p_patient_id) then
    raise exception 'unknown patient';
  end if;
  insert into public.break_glass_grants (patient_id, clinician_id, reason, expires_at)
  values (p_patient_id, v_uid, trim(p_reason), v_expires);
  return v_expires;
end
$$;
