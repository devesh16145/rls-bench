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
alter table public.lab_results enable row level security;

create policy patients_select on public.patients
  for select to authenticated
  using (user_id = auth.uid() or private.in_care_team(id));

create policy care_team_select on public.care_team
  for select to authenticated
  using (doctor_id = auth.uid() or private.is_patient(patient_id));

create policy lab_results_select on public.lab_results
  for select to authenticated
  using (
    (private.is_patient(patient_id) and released_at is not null)
    or private.in_care_team(patient_id)
  );

create policy lab_results_insert on public.lab_results
  for insert to authenticated
  with check (private.in_care_team(patient_id));

create policy lab_results_update on public.lab_results
  for update to authenticated
  using (private.in_care_team(patient_id) and (released_at is null or released_at > now()))
  with check (private.in_care_team(patient_id));
