create schema private;

grant usage on schema private to authenticated;

create function private.camera_owner(p_camera_id bigint) returns uuid
language sql stable security definer set search_path = ''
as $$
  select c.owner_id from public.cameras c where c.id = p_camera_id
$$;

create function private.has_live_share(p_camera_id bigint) returns boolean
language sql stable security definer set search_path = ''
as $$
  select exists (select 1 from public.camera_shares s where s.camera_id = p_camera_id and s.grantee_id = auth.uid() and (s.expires_at is null or s.expires_at > now()))
$$;

alter table public.cameras enable row level security;
alter table public.camera_shares enable row level security;
alter table public.stream_keys enable row level security;

create policy cameras_select on public.cameras
  for select to authenticated
  using (owner_id = auth.uid() or private.has_live_share(id));

create policy cameras_insert on public.cameras
  for insert to authenticated
  with check (owner_id = auth.uid());

create policy cameras_update on public.cameras
  for update to authenticated
  using (owner_id = auth.uid())
  with check (owner_id = auth.uid());

create policy shares_select on public.camera_shares
  for select to authenticated
  using (grantee_id = auth.uid() or private.camera_owner(camera_id) = auth.uid());

create policy shares_insert on public.camera_shares
  for insert to authenticated
  with check ((private.camera_owner(camera_id) = auth.uid() or private.has_live_share(camera_id)) and created_by = auth.uid());

create policy shares_delete on public.camera_shares
  for delete to authenticated
  using (private.camera_owner(camera_id) = auth.uid());

create policy stream_keys_select on public.stream_keys
  for select to authenticated
  using (
    (private.camera_owner(camera_id) = auth.uid() or private.has_live_share(camera_id))
    and (auth.jwt() ->> 'aal') = 'aal2'
  );
