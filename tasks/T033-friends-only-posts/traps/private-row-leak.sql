create schema private;

grant usage on schema private to anon, authenticated;

create function private.are_friends(p_other uuid) returns boolean
language sql stable security definer set search_path = ''
as $$
  select exists (
    select 1 from public.friendships f
    where ((f.requester_id = auth.uid() and f.addressee_id = p_other)
        or (f.addressee_id = auth.uid() and f.requester_id = p_other))
  )
$$;

alter table public.friendships enable row level security;
alter table public.posts enable row level security;

revoke update on public.friendships from anon, authenticated;
grant update (status) on public.friendships to authenticated;

create policy posts_select on public.posts
  for select to anon, authenticated
  using (
    audience = 'public'
    or author_id = auth.uid()
    or (audience = 'friends' and private.are_friends(author_id))
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

create policy friendships_select on public.friendships
  for select to authenticated
  using (requester_id = auth.uid() or addressee_id = auth.uid());

create policy friendships_insert on public.friendships
  for insert to authenticated
  with check (requester_id = auth.uid() and status = 'pending');

create policy friendships_update on public.friendships
  for update to authenticated
  using (addressee_id = auth.uid() and status = 'pending')
  with check (addressee_id = auth.uid() and status = 'accepted');

create policy friendships_delete on public.friendships
  for delete to authenticated
  using (requester_id = auth.uid() or addressee_id = auth.uid());
