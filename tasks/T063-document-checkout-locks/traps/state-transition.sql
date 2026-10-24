create schema private;

grant usage on schema private to authenticated;

create function private.can_read(p_doc_id bigint) returns boolean
language sql stable security definer set search_path = ''
as $$
  select exists (select 1 from public.doc_access a where a.doc_id = p_doc_id and a.user_id = auth.uid())
$$;

alter table public.documents enable row level security;
alter table public.doc_access enable row level security;

create policy documents_select on public.documents
  for select to authenticated
  using (private.can_read(id));

create policy doc_access_select on public.doc_access
  for select to authenticated
  using (user_id = auth.uid());

create function public.checkout_document(p_doc_id bigint) returns void
language plpgsql security definer set search_path = ''
as $$
declare
  v_uid uuid := auth.uid();
  v_doc public.documents%rowtype;
begin
  if v_uid is null or not exists (
    select 1 from public.doc_access a where a.doc_id = p_doc_id and a.user_id = v_uid and a.can_edit
  ) then
    raise exception 'no edit access';
  end if;
  select * into v_doc from public.documents where id = p_doc_id for update;
  if not found then
    raise exception 'unknown document';
  end if;
  update public.documents set checked_out_by = v_uid where id = p_doc_id;
end
$$;

create function public.checkin_document(p_doc_id bigint, p_body text) returns void
language plpgsql security definer set search_path = ''
as $$
declare
  v_uid uuid := auth.uid();
begin
  update public.documents
  set body = p_body, checked_out_by = null
  where id = p_doc_id and checked_out_by = v_uid and v_uid is not null;
  if not found then
    raise exception 'document is not checked out by you';
  end if;
end
$$;
