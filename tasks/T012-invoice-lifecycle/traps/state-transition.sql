create schema private;

grant usage on schema private to authenticated;

create function private.is_finance() returns boolean
language sql stable security definer set search_path = ''
as $$
  select exists (select 1 from public.finance_staff f where f.user_id = auth.uid())
$$;

create function private.invoice_guard() returns trigger
language plpgsql security definer set search_path = ''
as $$
begin
  if auth.role() = 'service_role' then
    return new;
  end if;
  if new.created_by is distinct from old.created_by then
    raise exception 'created_by cannot change';
  end if;
  if old.status <> 'draft'
     and (new.customer is distinct from old.customer or new.amount is distinct from old.amount) then
    raise exception 'invoice % is locked', old.id;
  end if;
  return new;
end
$$;

create trigger invoices_guard
  before update on public.invoices
  for each row execute function private.invoice_guard();

alter table public.finance_staff enable row level security;
alter table public.invoices enable row level security;

create policy finance_staff_select on public.finance_staff
  for select to authenticated
  using (user_id = auth.uid());

create policy invoices_select on public.invoices
  for select to authenticated
  using (created_by = auth.uid() or private.is_finance());

create policy invoices_insert on public.invoices
  for insert to authenticated
  with check (created_by = auth.uid() and status = 'draft');

create policy invoices_update on public.invoices
  for update to authenticated
  using (created_by = auth.uid() or private.is_finance())
  with check (created_by = auth.uid() or private.is_finance());

create policy invoices_delete on public.invoices
  for delete to authenticated
  using (created_by = auth.uid() and status = 'draft');
