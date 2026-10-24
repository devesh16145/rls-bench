alter table public.recipes enable row level security;
alter table public.favorites enable row level security;

create policy recipes_select on public.recipes
  for select to anon, authenticated
  using (is_public or author_id = auth.uid());

create policy recipes_insert on public.recipes
  for insert to authenticated
  with check (author_id = auth.uid());

create policy recipes_update on public.recipes
  for update to authenticated
  using (author_id = auth.uid())
  with check (author_id = auth.uid());

create policy recipes_delete on public.recipes
  for delete to authenticated
  using (author_id = auth.uid());

create policy favorites_select on public.favorites
  for select to authenticated
  using (user_id = auth.uid());

create policy favorites_insert on public.favorites
  for insert to authenticated
  with check (
    user_id = auth.uid()
    and exists (select 1 from public.recipes r where r.id = recipe_id and (r.is_public or r.author_id = auth.uid()))
  );

create policy favorites_delete on public.favorites
  for delete to authenticated
  using (user_id = auth.uid());
