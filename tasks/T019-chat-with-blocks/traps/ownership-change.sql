create schema private;

grant usage on schema private to authenticated;

create function private.is_participant(p_conversation_id bigint) returns boolean
language sql stable security definer set search_path = ''
as $$
  select exists (
    select 1 from public.participants p
    where p.conversation_id = p_conversation_id and p.user_id = auth.uid()
  )
$$;

create function private.blocked_in(p_conversation_id bigint) returns boolean
language sql stable security definer set search_path = ''
as $$
  select exists (
    select 1
    from public.participants p
    join public.blocks b on b.blocker_id = p.user_id
    where p.conversation_id = p_conversation_id and b.blocked_id = auth.uid()
  )
$$;

create function private.message_conversation(p_message_id bigint) returns bigint
language sql stable security definer set search_path = ''
as $$
  select m.conversation_id from public.messages m where m.id = p_message_id
$$;

alter table public.conversations enable row level security;
alter table public.participants enable row level security;
alter table public.messages enable row level security;
alter table public.blocks enable row level security;

create policy conversations_select on public.conversations
  for select to authenticated
  using (private.is_participant(id));

create policy participants_select on public.participants
  for select to authenticated
  using (private.is_participant(conversation_id));

create policy messages_select on public.messages
  for select to authenticated
  using (private.is_participant(conversation_id));

create policy messages_insert on public.messages
  for insert to authenticated
  with check (
    sender_id = auth.uid()
    and private.is_participant(conversation_id)
    and not private.blocked_in(conversation_id)
  );

create policy messages_update on public.messages
  for update to authenticated
  using (sender_id = auth.uid())
  with check (sender_id = auth.uid() and private.is_participant(conversation_id));

create policy messages_delete on public.messages
  for delete to authenticated
  using (sender_id = auth.uid());

create policy blocks_select on public.blocks
  for select to authenticated
  using (blocker_id = auth.uid());

create policy blocks_insert on public.blocks
  for insert to authenticated
  with check (blocker_id = auth.uid());

create policy blocks_delete on public.blocks
  for delete to authenticated
  using (blocker_id = auth.uid());
