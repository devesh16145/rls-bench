create schema private;

grant usage on schema private to authenticated;

create function private.is_patient(p_patient_id bigint) returns boolean
language sql stable security definer set search_path = ''
as $$
  select exists (select 1 from public.patients p where p.id = p_patient_id and p.user_id = auth.uid())
$$;

create function private.in_care_team(p_patient_id bigint) returns boolean
language sql stable security definer set search_path = ''
as $$
  select exists (select 1 from public.care_team c where c.patient_id = p_patient_id and c.doctor_id = auth.uid())
$$;

alter table public.patients enable row level security;
alter table public.care_team enable row level security;
alter table public.records enable row level security;

create policy patients_select on public.patients
  for select to authenticated
  using (
    user_id = auth.uid()
    or (private.in_care_team(id) and (auth.jwt() ->> 'aal') = 'aal2')
  );

create policy care_team_select on public.care_team
  for select to authenticated
  using (doctor_id = auth.uid() or private.is_patient(patient_id));

create policy records_select on public.records
  for select to authenticated
  using (
    private.is_patient(patient_id)
    or (
      (private.in_care_team(patient_id) or (auth.jwt() -> 'user_metadata' ->> 'role') = 'doctor')
      and (auth.jwt() ->> 'aal') = 'aal2'
    )
  );

create policy records_insert on public.records
  for insert to authenticated
  with check (
    author_id = auth.uid()
    and private.in_care_team(patient_id)
    and (auth.jwt() ->> 'aal') = 'aal2'
  );
