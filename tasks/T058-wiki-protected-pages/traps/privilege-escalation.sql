create schema private;

grant usage on schema private to anon, authenticated;

create function private.is_editor() returns boolean
language sql stable security definer set search_path = ''
as $$
  select exists (select 1 from public.editors e where e.user_id = auth.uid())
$$;

create function private.page_protected(p_slug text) returns boolean
language sql stable security definer set search_path = ''
as $$
  select coalesce((select p.is_protected from public.pages p where p.slug = p_slug), true)
$$;

alter table public.editors enable row level security;
alter table public.pages enable row level security;
alter table public.page_revisions enable row level security;

create policy editors_select on public.editors
  for select to authenticated
  using (true);

create policy pages_select on public.pages
  for select to anon, authenticated
  using (true);

create policy pages_insert on public.pages
  for insert to authenticated
  with check (updated_by = auth.uid() and (not is_protected or private.is_editor()));

create policy pages_update on public.pages
  for update to authenticated
  using (not is_protected or private.is_editor())
  with check (updated_by = auth.uid());

create policy revisions_select on public.page_revisions
  for select to anon, authenticated
  using (true);

create policy revisions_insert on public.page_revisions
  for insert to authenticated
  with check (author_id = auth.uid() and (private.is_editor() or not private.page_protected(slug)));
