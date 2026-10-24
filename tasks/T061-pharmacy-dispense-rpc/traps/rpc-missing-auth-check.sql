create schema private;

grant usage on schema private to authenticated;

create function private.is_pharmacist() returns boolean
language sql stable security definer set search_path = ''
as $$
  select exists (select 1 from public.pharmacists p where p.user_id = auth.uid())
$$;

alter table public.pharmacists enable row level security;
alter table public.prescriptions enable row level security;
alter table public.dispenses enable row level security;

create policy pharmacists_select on public.pharmacists
  for select to authenticated
  using (true);

create policy prescriptions_select on public.prescriptions
  for select to authenticated
  using (patient_id = auth.uid() or private.is_pharmacist());

create policy dispenses_select on public.dispenses
  for select to authenticated
  using (
    private.is_pharmacist()
    or exists (select 1 from public.prescriptions p where p.id = prescription_id and p.patient_id = auth.uid())
  );

create function public.dispense(p_prescription_id bigint) returns integer
language plpgsql security definer set search_path = ''
as $$
declare
  v_uid uuid := auth.uid();
  v_rx public.prescriptions%rowtype;
begin
  select * into v_rx from public.prescriptions where id = p_prescription_id for update;
  if not found then
    raise exception 'unknown prescription';
  end if;
  if v_rx.patient_id = v_uid then
    raise exception 'pharmacists cannot dispense their own prescriptions';
  end if;
  if v_rx.expires_at <= now() then
    raise exception 'prescription expired';
  end if;
  if v_rx.refills_left <= 0 then
    raise exception 'no refills left';
  end if;
  update public.prescriptions set refills_left = refills_left - 1 where id = p_prescription_id;
  insert into public.dispenses (prescription_id, pharmacist_id) values (p_prescription_id, v_uid);
  return v_rx.refills_left - 1;
end
$$;
