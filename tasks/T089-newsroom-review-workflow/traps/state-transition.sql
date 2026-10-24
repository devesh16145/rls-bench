create schema private;

grant usage on schema private to anon, authenticated;

create function private.is_editor() returns boolean
language sql stable security definer set search_path = ''
as $$
  select exists (select 1 from public.editors e where e.user_id = auth.uid())
$$;

alter table public.editors enable row level security;
alter table public.articles enable row level security;

create policy editors_select on public.editors
  for select to authenticated
  using (user_id = auth.uid());

create policy articles_select on public.articles
  for select to anon, authenticated
  using (status = 'published' or author_id = auth.uid() or private.is_editor());

create policy articles_insert on public.articles
  for insert to authenticated
  with check (author_id = auth.uid() and status = 'draft' and published_at is null);

create policy articles_writer_update on public.articles
  for update to authenticated
  using (author_id = auth.uid() and status = 'draft')
  with check (author_id = auth.uid());

create policy articles_editor_update on public.articles
  for update to authenticated
  using (private.is_editor() and status = 'in_review')
  with check (private.is_editor() and status in ('draft', 'in_review', 'published'));

create policy articles_delete on public.articles
  for delete to authenticated
  using (author_id = auth.uid() and status = 'draft');
