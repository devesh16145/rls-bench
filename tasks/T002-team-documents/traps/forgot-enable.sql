alter table public.teams enable row level security;
alter table public.documents enable row level security;

create policy teams_select on public.teams
  for select to authenticated
  using (exists (
    select 1 from public.team_members m
    where m.team_id = teams.id and m.user_id = auth.uid()
  ));

create policy team_members_select on public.team_members
  for select to authenticated
  using (user_id = auth.uid());

create policy documents_select on public.documents
  for select to authenticated
  using (
    deleted_at is null
    and exists (
      select 1 from public.team_members m
      where m.team_id = documents.team_id and m.user_id = auth.uid()
    )
  );

create policy documents_insert on public.documents
  for insert to authenticated
  with check (
    created_by = auth.uid()
    and exists (
      select 1 from public.team_members m
      where m.team_id = documents.team_id and m.user_id = auth.uid() and m.role = 'editor'
    )
  );

create policy documents_update on public.documents
  for update to authenticated
  using (
    deleted_at is null
    and exists (
      select 1 from public.team_members m
      where m.team_id = documents.team_id and m.user_id = auth.uid() and m.role = 'editor'
    )
  )
  with check (
    exists (
      select 1 from public.team_members m
      where m.team_id = documents.team_id and m.user_id = auth.uid() and m.role = 'editor'
    )
  );

create policy documents_delete on public.documents
  for delete to authenticated
  using (created_by = auth.uid());
