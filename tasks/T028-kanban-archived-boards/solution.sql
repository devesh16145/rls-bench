create schema private;

grant usage on schema private to authenticated;

create function private.board_role(p_board_id bigint) returns text
language sql stable security definer set search_path = ''
as $$
  select m.role from public.board_members m where m.board_id = p_board_id and m.user_id = auth.uid()
$$;

create function private.board_archived(p_board_id bigint) returns boolean
language sql stable security definer set search_path = ''
as $$
  select coalesce((select b.is_archived from public.boards b where b.id = p_board_id), true)
$$;

alter table public.boards enable row level security;
alter table public.board_members enable row level security;
alter table public.cards enable row level security;

create policy boards_select on public.boards
  for select to authenticated
  using (private.board_role(id) is not null);

create policy board_members_select on public.board_members
  for select to authenticated
  using (private.board_role(board_id) is not null);

create policy cards_select on public.cards
  for select to authenticated
  using (private.board_role(board_id) is not null);

create policy cards_insert on public.cards
  for insert to authenticated
  with check (private.board_role(board_id) = 'editor' and not private.board_archived(board_id));

create policy cards_update on public.cards
  for update to authenticated
  using (private.board_role(board_id) = 'editor' and not private.board_archived(board_id))
  with check (private.board_role(board_id) = 'editor' and not private.board_archived(board_id));

create policy cards_delete on public.cards
  for delete to authenticated
  using (private.board_role(board_id) = 'editor' and not private.board_archived(board_id));
