alter table public.notifications enable row level security;

revoke update on public.notifications from anon, authenticated;
grant update (read_at) on public.notifications to authenticated;

create policy notifications_own on public.notifications
  for all to authenticated
  using (user_id = auth.uid())
  with check (user_id = auth.uid());
