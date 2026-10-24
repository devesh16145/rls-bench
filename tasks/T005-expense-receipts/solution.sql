alter table public.receipts enable row level security;

create policy receipts_select on public.receipts
  for select to authenticated
  using (uploaded_by = auth.uid());

create policy receipts_insert on public.receipts
  for insert to authenticated
  with check (uploaded_by = auth.uid());

create policy receipts_update on public.receipts
  for update to authenticated
  using (uploaded_by = auth.uid())
  with check (uploaded_by = auth.uid());

create policy receipts_delete on public.receipts
  for delete to authenticated
  using (uploaded_by = auth.uid());
