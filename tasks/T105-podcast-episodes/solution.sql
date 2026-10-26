create schema private;

grant usage on schema private to anon, authenticated;

create function private.is_host(p_show_id bigint) returns boolean
language sql stable security definer set search_path = ''
as $$
  select exists (select 1 from public.hosts h where h.show_id = p_show_id and h.user_id = auth.uid())
$$;

alter table public.shows enable row level security;
alter table public.hosts enable row level security;
alter table public.episodes enable row level security;

create policy shows_select on public.shows
  for select to anon, authenticated
  using (true);

create policy hosts_select on public.hosts
  for select to authenticated
  using (user_id = auth.uid());

create policy episodes_public_select on public.episodes
  for select to anon, authenticated
  using (status = 'published' and publish_at <= now());

create policy episodes_host_select on public.episodes
  for select to authenticated
  using (private.is_host(show_id));

create policy episodes_insert on public.episodes
  for insert to authenticated
  with check (private.is_host(show_id) and created_by = auth.uid());

create policy episodes_update on public.episodes
  for update to authenticated
  using (private.is_host(show_id))
  with check (private.is_host(show_id));

create policy episodes_delete on public.episodes
  for delete to authenticated
  using (private.is_host(show_id) and status = 'draft');
