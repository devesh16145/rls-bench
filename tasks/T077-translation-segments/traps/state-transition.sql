create schema private;

grant usage on schema private to authenticated;

create function private.lang_role(p_project_id bigint, p_lang text) returns text
language sql stable security definer set search_path = ''
as $$
  select t.role from public.translators t where t.project_id = p_project_id and t.lang = p_lang and t.user_id = auth.uid()
$$;

alter table public.projects enable row level security;
alter table public.translators enable row level security;
alter table public.segments enable row level security;

revoke update on public.segments from anon, authenticated;
grant update (target_text, status, translated_by) on public.segments to authenticated;

create policy projects_select on public.projects
  for select to authenticated
  using (exists (select 1 from public.translators t where t.project_id = id and t.user_id = auth.uid()));

create policy translators_select on public.translators
  for select to authenticated
  using (user_id = auth.uid());

create policy segments_select on public.segments
  for select to authenticated
  using (private.lang_role(project_id, lang) is not null);

create policy segments_update on public.segments
  for update to authenticated
  using (status = 'draft' and private.lang_role(project_id, lang) is not null)
  with check (
    private.lang_role(project_id, lang) = 'reviewer'
    or (private.lang_role(project_id, lang) = 'translator' and translated_by = auth.uid())
  );
