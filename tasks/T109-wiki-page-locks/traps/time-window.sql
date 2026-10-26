create schema private;

grant usage on schema private to authenticated;

create function private.is_member(p_space_id bigint) returns boolean
language sql stable security definer set search_path = ''
as $$
  select exists (select 1 from public.members m where m.space_id = p_space_id and m.user_id = auth.uid())
$$;

alter table public.spaces enable row level security;
alter table public.members enable row level security;
alter table public.pages enable row level security;

revoke update on public.pages from anon, authenticated;
grant update (title, body, locked_by, locked_until) on public.pages to authenticated;

create policy spaces_select on public.spaces
  for select to authenticated
  using (private.is_member(id));

create policy members_select on public.members
  for select to authenticated
  using (user_id = auth.uid());

create policy pages_select on public.pages
  for select to authenticated
  using (private.is_member(space_id));

create policy pages_insert on public.pages
  for insert to authenticated
  with check (private.is_member(space_id) and locked_by is null and locked_until is null);

create policy pages_update on public.pages
  for update to authenticated
  using (
    private.is_member(space_id)
    and (locked_by is null or locked_by = auth.uid() or locked_until <= now())
  )
  with check (
    private.is_member(space_id)
    and locked_by = auth.uid()
    and locked_until > now()
  );
