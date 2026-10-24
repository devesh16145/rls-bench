create schema private;

grant usage on schema private to authenticated;

create function private.poll_open(p_poll_id bigint) returns boolean
language sql stable security definer set search_path = ''
as $$
  select coalesce((select p.closes_at > now() from public.polls p where p.id = p_poll_id), false)
$$;

create function private.option_in_poll(p_option_id bigint, p_poll_id bigint) returns boolean
language sql stable security definer set search_path = ''
as $$
  select exists (select 1 from public.poll_options o where o.id = p_option_id and o.poll_id = p_poll_id)
$$;

alter table public.polls enable row level security;
alter table public.poll_options enable row level security;
alter table public.votes enable row level security;

create policy polls_select on public.polls
  for select to authenticated
  using (true);

create policy poll_options_select on public.poll_options
  for select to authenticated
  using (true);

create policy votes_select on public.votes
  for select to authenticated
  using (user_id = auth.uid());

create policy votes_insert on public.votes
  for insert to authenticated
  with check (user_id = auth.uid() and private.option_in_poll(option_id, poll_id));

create policy votes_update on public.votes
  for update to authenticated
  using (user_id = auth.uid() and private.poll_open(poll_id))
  with check (user_id = auth.uid() and private.poll_open(poll_id) and private.option_in_poll(option_id, poll_id));

create policy votes_delete on public.votes
  for delete to authenticated
  using (user_id = auth.uid() and private.poll_open(poll_id));
