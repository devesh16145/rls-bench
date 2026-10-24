create schema private;

grant usage on schema private to authenticated;

create function private.is_suspended() returns boolean
language sql stable security definer set search_path = ''
as $$
  select exists (select 1 from public.accounts a where a.user_id = auth.uid() and a.suspended)
$$;

create function private.file_owner(p_file_id bigint) returns uuid
language sql stable security definer set search_path = ''
as $$
  select f.owner_id from public.files f where f.id = p_file_id
$$;

create function private.has_share(p_file_id bigint, p_edit boolean) returns boolean
language sql stable security definer set search_path = ''
as $$
  select exists (
    select 1 from public.file_shares s
    where s.file_id = p_file_id
      and s.shared_with = auth.uid()
      and (s.expires_at is null or s.expires_at > now())
      and (s.can_edit or not p_edit)
  )
$$;

alter table public.accounts enable row level security;
alter table public.files enable row level security;
alter table public.file_shares enable row level security;

create policy accounts_select on public.accounts
  for select to authenticated
  using (user_id = auth.uid());

create policy files_select on public.files
  for select to authenticated
  using (owner_id = auth.uid() or private.has_share(id, false));

create policy files_insert on public.files
  for insert to authenticated
  with check (owner_id = auth.uid());

create policy files_update on public.files
  for update to authenticated
  using (owner_id = auth.uid() or private.has_share(id, true))
  with check (
    owner_id = private.file_owner(id)
    and (owner_id = auth.uid() or private.has_share(id, true))
  );

create policy files_delete on public.files
  for delete to authenticated
  using (owner_id = auth.uid());

create policy files_not_suspended on public.files
  as restrictive
  for all to authenticated
  using (not private.is_suspended())
  with check (not private.is_suspended());

create policy file_shares_select on public.file_shares
  for select to authenticated
  using (shared_with = auth.uid() or private.file_owner(file_id) = auth.uid());

create policy file_shares_insert on public.file_shares
  for insert to authenticated
  with check (private.file_owner(file_id) = auth.uid());

create policy file_shares_update on public.file_shares
  for update to authenticated
  using (private.file_owner(file_id) = auth.uid())
  with check (private.file_owner(file_id) = auth.uid());

create policy file_shares_delete on public.file_shares
  for delete to authenticated
  using (private.file_owner(file_id) = auth.uid());

create policy file_shares_not_suspended on public.file_shares
  as restrictive
  for all to authenticated
  using (not private.is_suspended())
  with check (not private.is_suspended());
