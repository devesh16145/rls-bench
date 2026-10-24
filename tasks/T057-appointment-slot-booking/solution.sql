alter table public.providers enable row level security;
alter table public.slots enable row level security;

revoke update on public.slots from anon, authenticated;
grant update (booked_by) on public.slots to authenticated;

create policy providers_select on public.providers
  for select to authenticated
  using (true);

create policy slots_select on public.slots
  for select to authenticated
  using (
    (booked_by is null and starts_at > now())
    or booked_by = auth.uid()
    or provider_id = auth.uid()
  );

create policy slots_update on public.slots
  for update to authenticated
  using (starts_at > now() and (booked_by is null or booked_by = auth.uid()))
  with check (starts_at > now() and (booked_by is null or booked_by = auth.uid()));
