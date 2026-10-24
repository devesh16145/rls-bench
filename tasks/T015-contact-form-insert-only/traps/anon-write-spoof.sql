alter table public.contact_messages enable row level security;

create policy contact_messages_insert on public.contact_messages
  for insert to anon, authenticated
  with check (true);
