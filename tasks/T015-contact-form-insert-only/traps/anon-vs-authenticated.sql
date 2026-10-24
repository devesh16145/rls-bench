alter table public.contact_messages enable row level security;

create policy contact_messages_insert on public.contact_messages
  for insert to authenticated
  with check (status = 'new' and handled_by is null);
