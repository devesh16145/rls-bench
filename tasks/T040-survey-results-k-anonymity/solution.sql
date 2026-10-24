alter table public.surveys enable row level security;
alter table public.survey_responses enable row level security;

create policy surveys_select on public.surveys
  for select to authenticated
  using (true);

create policy surveys_insert on public.surveys
  for insert to authenticated
  with check (owner_id = auth.uid());

create policy surveys_update on public.surveys
  for update to authenticated
  using (owner_id = auth.uid())
  with check (owner_id = auth.uid());

create policy responses_select on public.survey_responses
  for select to authenticated
  using (respondent_id = auth.uid());

create policy responses_insert on public.survey_responses
  for insert to authenticated
  with check (respondent_id = auth.uid());

create policy responses_update on public.survey_responses
  for update to authenticated
  using (respondent_id = auth.uid())
  with check (respondent_id = auth.uid());

create view public.survey_results as
  select r.survey_id, count(*)::integer as responses, round(avg(r.score), 2) as avg_score
  from public.survey_responses r
  join public.surveys s on s.id = r.survey_id
  where s.owner_id = auth.uid() or auth.role() = 'service_role'
  group by r.survey_id
  having count(*) >= 3;
