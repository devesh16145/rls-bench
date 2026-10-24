alter table public.notifications enable row level security;

revoke update on public.notifications from anon, authenticated;
grant update (read_at) on public.notifications to authenticated;

create policy notifications_select on public.notifications
  for select to authenticated
  using (user_id = auth.uid());

create policy notifications_update on public.notifications
  for update to authenticated
  using (user_id = auth.uid())
  with check (user_id = auth.uid());

create policy notifications_delete on public.notifications
  for delete to authenticated
  using (user_id = auth.uid());
