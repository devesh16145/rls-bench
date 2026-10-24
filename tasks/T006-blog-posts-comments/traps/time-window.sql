alter table public.posts enable row level security;
alter table public.comments enable row level security;

create policy posts_select on public.posts
  for select to anon, authenticated
  using (
    published_at is not null
    or author_id = auth.uid()
  );

create policy posts_insert on public.posts
  for insert to authenticated
  with check (author_id = auth.uid());

create policy posts_update on public.posts
  for update to authenticated
  using (author_id = auth.uid())
  with check (author_id = auth.uid());

create policy posts_delete on public.posts
  for delete to authenticated
  using (author_id = auth.uid());

create policy comments_select on public.comments
  for select to anon, authenticated
  using (exists (select 1 from public.posts p where p.id = comments.post_id));

create policy comments_insert on public.comments
  for insert to authenticated
  with check (
    author_id = auth.uid()
    and exists (select 1 from public.posts p where p.id = comments.post_id)
  );

create policy comments_delete on public.comments
  for delete to authenticated
  using (
    author_id = auth.uid()
    or exists (select 1 from public.posts p where p.id = comments.post_id and p.author_id = auth.uid())
  );
