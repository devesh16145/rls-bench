alter table public.emails enable row level security;

create policy emails_select on public.emails
  for select to authenticated
  using (user_id = auth.uid());

create policy emails_insert on public.emails
  for insert to authenticated
  with check (user_id = auth.uid() and sent_at is null);

create policy emails_update on public.emails
  for update to authenticated
  using (user_id = auth.uid())
  with check (user_id = auth.uid() and sent_at is null);

create policy emails_delete on public.emails
  for delete to authenticated
  using (user_id = auth.uid());
