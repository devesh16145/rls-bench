create policy invoices_select on storage.objects
  for select to authenticated
  using (bucket_id = 'invoices' and owner = auth.uid());

create policy invoices_insert on storage.objects
  for insert to authenticated
  with check (bucket_id = 'invoices' and owner = auth.uid() and name like '%.pdf' and owner = auth.uid());

create policy invoices_update on storage.objects
  for update to authenticated
  using (bucket_id = 'invoices' and owner = auth.uid())
  with check (bucket_id = 'invoices' and owner = auth.uid() and name like '%.pdf' and owner = auth.uid());

create policy invoices_delete on storage.objects
  for delete to authenticated
  using (bucket_id = 'invoices' and owner = auth.uid());
