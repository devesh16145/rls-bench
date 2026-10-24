create schema private;

grant usage on schema private to authenticated;

create function private.is_reviewer() returns boolean
language sql stable security definer set search_path = ''
as $$
  select exists (select 1 from public.reviewers r where r.user_id = auth.uid())
$$;

create function private.proposal_speaker(p_proposal_id bigint) returns uuid
language sql stable security definer set search_path = ''
as $$
  select p.speaker_id from public.proposals p where p.id = p_proposal_id
$$;

create function private.proposal_status(p_proposal_id bigint) returns text
language sql stable security definer set search_path = ''
as $$
  select p.status from public.proposals p where p.id = p_proposal_id
$$;

alter table public.reviewers enable row level security;
alter table public.proposals enable row level security;
alter table public.reviews enable row level security;

create policy reviewers_select on public.reviewers
  for select to authenticated
  using (user_id = auth.uid());

create policy proposals_select on public.proposals
  for select to authenticated
  using (speaker_id = auth.uid() or private.is_reviewer());

create policy proposals_insert on public.proposals
  for insert to authenticated
  with check (speaker_id = auth.uid() and status = 'submitted');

create policy proposals_update on public.proposals
  for update to authenticated
  using (speaker_id = auth.uid() and status = 'submitted')
  with check (speaker_id = auth.uid() and status = 'submitted');

create policy reviews_select on public.reviews
  for select to authenticated
  using (
    reviewer_id = auth.uid()
    or (private.proposal_speaker(proposal_id) = auth.uid() and private.proposal_status(proposal_id) <> 'submitted')
  );

create policy reviews_insert on public.reviews
  for insert to authenticated
  with check (
    reviewer_id = auth.uid()
    and private.is_reviewer()
    and private.proposal_status(proposal_id) = 'submitted'
  );

create policy reviews_update on public.reviews
  for update to authenticated
  using (reviewer_id = auth.uid() and private.proposal_status(proposal_id) = 'submitted')
  with check (reviewer_id = auth.uid() and private.proposal_status(proposal_id) = 'submitted');
