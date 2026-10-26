create schema private;

grant usage on schema private to authenticated;

create function private.bounty_poster(p_bounty_id bigint) returns uuid
language sql stable security definer set search_path = ''
as $$
  select b.poster_id from public.bounties b where b.id = p_bounty_id
$$;

create function private.bounty_open(p_bounty_id bigint) returns boolean
language sql stable security definer set search_path = ''
as $$
  select exists (select 1 from public.bounties b where b.id = p_bounty_id and b.status = 'open')
$$;

create function private.already_submitted(p_bounty_id bigint) returns boolean
language sql stable security definer set search_path = ''
as $$
  select exists (select 1 from public.submissions s where s.bounty_id = p_bounty_id and s.submitter_id = auth.uid())
$$;

create function private.submission_of_bounty(p_submission_id bigint, p_bounty_id bigint) returns boolean
language sql stable security definer set search_path = ''
as $$
  select exists (select 1 from public.submissions s where s.id = p_submission_id and s.bounty_id = p_bounty_id)
$$;

alter table public.bounties enable row level security;
alter table public.submissions enable row level security;

revoke update on public.submissions from anon, authenticated;
grant update (body) on public.submissions to authenticated;

create policy bounties_select on public.bounties
  for select to authenticated
  using (true);

create policy bounties_insert on public.bounties
  for insert to authenticated
  with check (poster_id = auth.uid() and status = 'open' and awarded_submission_id is null);

create policy bounties_update on public.bounties
  for update to authenticated
  using (poster_id = auth.uid() and status = 'open')
  with check (
    poster_id = auth.uid()
    and (
      (status = 'open' and awarded_submission_id is null)
      or (status = 'awarded' and private.submission_of_bounty(awarded_submission_id, id))
    )
  );

create policy submissions_select on public.submissions
  for select to authenticated
  using (submitter_id = auth.uid() or private.bounty_poster(bounty_id) = auth.uid());

create policy submissions_insert on public.submissions
  for insert to authenticated
  with check (
    submitter_id = auth.uid()
    and private.bounty_open(bounty_id)
    and private.bounty_poster(bounty_id) <> auth.uid()
    and not private.already_submitted(bounty_id)
  );

create policy submissions_update on public.submissions
  for update to authenticated
  using (submitter_id = auth.uid() and private.bounty_open(bounty_id))
  with check (submitter_id = auth.uid() and private.bounty_open(bounty_id));
