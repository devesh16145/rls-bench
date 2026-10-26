alter table public.events enable row level security;
alter table public.seats enable row level security;

create policy events_select on public.events
  for select to authenticated
  using (true);

create policy seats_select_own on public.seats
  for select to authenticated
  using (true);

create view public.seat_map as
select
  s.id,
  s.event_id,
  s.label,
  case when s.status = 'held' and s.hold_until <= now() then 'free' else s.status end as status
from public.seats s;

revoke all on public.seat_map from anon;
grant select on public.seat_map to authenticated;

create function public.hold_seat(p_seat_id bigint) returns void
language plpgsql security definer set search_path = ''
as $$
begin
  if auth.uid() is null then
    raise exception 'not signed in';
  end if;
  update public.seats
  set status = 'held', holder_id = auth.uid(), hold_until = now() + interval '10 minutes'
  where id = p_seat_id
    and (status = 'free' or (status = 'held' and hold_until <= now()));
  if not found then
    raise exception 'seat is not available';
  end if;
end;
$$;

create function public.confirm_seat(p_seat_id bigint) returns void
language plpgsql security definer set search_path = ''
as $$
begin
  if auth.uid() is null then
    raise exception 'not signed in';
  end if;
  update public.seats
  set status = 'booked', booked_by = auth.uid(), holder_id = null, hold_until = null
  where id = p_seat_id
    and status = 'held' and holder_id = auth.uid() and hold_until > now();
  if not found then
    raise exception 'no live hold on this seat';
  end if;
end;
$$;

revoke execute on function public.hold_seat(bigint) from public, anon;
revoke execute on function public.confirm_seat(bigint) from public, anon;
grant execute on function public.hold_seat(bigint) to authenticated;
grant execute on function public.confirm_seat(bigint) to authenticated;
