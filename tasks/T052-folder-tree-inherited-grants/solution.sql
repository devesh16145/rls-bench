create schema private;

grant usage on schema private to authenticated;

create function private.folder_access(p_folder_id bigint) returns text
language sql stable security definer set search_path = ''
as $$
  with recursive chain as (
    select f.id, f.parent_id, f.owner_id from public.folders f where f.id = p_folder_id
    union all
    select f.id, f.parent_id, f.owner_id from public.folders f join chain c on f.id = c.parent_id
  )
  select case
    when exists (select 1 from chain where owner_id = auth.uid()) then 'owner'
    when exists (select 1 from chain join public.folder_grants g on g.folder_id = chain.id where g.user_id = auth.uid() and g.can_edit) then 'edit'
    when exists (select 1 from chain join public.folder_grants g on g.folder_id = chain.id where g.user_id = auth.uid()) then 'read'
  end
$$;

alter table public.folders enable row level security;
alter table public.folder_grants enable row level security;
alter table public.documents enable row level security;

create policy folders_select on public.folders
  for select to authenticated
  using (owner_id = auth.uid() or private.folder_access(id) is not null);

create policy folders_insert on public.folders
  for insert to authenticated
  with check (owner_id = auth.uid() and (parent_id is null or private.folder_access(parent_id) = 'owner'));

create policy folder_grants_select on public.folder_grants
  for select to authenticated
  using (user_id = auth.uid() or private.folder_access(folder_id) = 'owner');

create policy folder_grants_insert on public.folder_grants
  for insert to authenticated
  with check (private.folder_access(folder_id) = 'owner');

create policy folder_grants_delete on public.folder_grants
  for delete to authenticated
  using (private.folder_access(folder_id) = 'owner');

create policy documents_select on public.documents
  for select to authenticated
  using (private.folder_access(folder_id) is not null);

create policy documents_insert on public.documents
  for insert to authenticated
  with check (private.folder_access(folder_id) in ('owner', 'edit'));

create policy documents_update on public.documents
  for update to authenticated
  using (private.folder_access(folder_id) in ('owner', 'edit'))
  with check (private.folder_access(folder_id) in ('owner', 'edit'));

create policy documents_delete on public.documents
  for delete to authenticated
  using (private.folder_access(folder_id) in ('owner', 'edit'));
