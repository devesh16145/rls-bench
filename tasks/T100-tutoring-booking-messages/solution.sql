create schema private;

grant usage on schema private to authenticated;

create function private.in_booking(p_booking_id bigint) returns boolean
language sql stable security definer set search_path = ''
as $$
  select exists (select 1 from public.bookings b where b.id = p_booking_id and (b.student_id = auth.uid() or b.tutor_id = auth.uid()))
$$;

create function private.booking_confirmed(p_booking_id bigint) returns boolean
language sql stable security definer set search_path = ''
as $$
  select coalesce((select b.status = 'confirmed' from public.bookings b where b.id = p_booking_id), false)
$$;

alter table public.bookings enable row level security;
alter table public.booking_messages enable row level security;

create policy bookings_select on public.bookings
  for select to authenticated
  using (student_id = auth.uid() or tutor_id = auth.uid());

create policy messages_select on public.booking_messages
  for select to authenticated
  using (private.in_booking(booking_id));

create policy messages_insert on public.booking_messages
  for insert to authenticated
  with check (sender_id = auth.uid() and private.in_booking(booking_id) and private.booking_confirmed(booking_id));

create policy messages_delete on public.booking_messages
  for delete to authenticated
  using (sender_id = auth.uid());
