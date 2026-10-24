create schema private;

grant usage on schema private to authenticated;

create function private.is_librarian() returns boolean
language sql stable security definer set search_path = ''
as $$
  select exists (select 1 from public.librarians l where l.user_id = auth.uid())
$$;

create function private.free_copies(p_book_id bigint) returns integer
language sql stable security definer set search_path = ''
as $$
  select b.copies - (
    select count(*)::integer from public.loans l where l.book_id = b.id and l.returned_on is null
  )
  from public.books b
  where b.id = p_book_id
$$;

create function private.my_active_loans() returns integer
language sql stable security definer set search_path = ''
as $$
  select count(*)::integer from public.loans l where l.borrower_id = auth.uid() and l.returned_on is null
$$;

alter table public.books enable row level security;
alter table public.librarians enable row level security;
alter table public.loans enable row level security;

revoke update on public.loans from anon, authenticated;
grant update (returned_on) on public.loans to authenticated;

create policy books_select on public.books
  for select to authenticated
  using (true);

create policy books_insert on public.books
  for insert to authenticated
  with check (private.is_librarian());

create policy books_update on public.books
  for update to authenticated
  using (private.is_librarian())
  with check (private.is_librarian());

create policy librarians_select on public.librarians
  for select to authenticated
  using (user_id = auth.uid());

create policy loans_select on public.loans
  for select to authenticated
  using (borrower_id = auth.uid() or private.is_librarian());

create policy loans_insert on public.loans
  for insert to authenticated
  with check (
    borrower_id = auth.uid()
    and returned_on is null
    and private.my_active_loans() < 3
  );

create policy loans_update on public.loans
  for update to authenticated
  using (borrower_id = auth.uid() and returned_on is null)
  with check (borrower_id = auth.uid() and returned_on is not null);
