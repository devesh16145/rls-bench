alter table public.receipts enable row level security;

create policy receipts_owner on public.receipts
  for all to public
  using (uploaded_by is not distinct from auth.uid())
  with check (uploaded_by is not distinct from auth.uid());
