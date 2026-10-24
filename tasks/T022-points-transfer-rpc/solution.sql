alter table public.wallets enable row level security;
alter table public.transfers enable row level security;

create policy wallets_select on public.wallets
  for select to authenticated
  using (user_id = auth.uid());

create policy transfers_select on public.transfers
  for select to authenticated
  using (from_user = auth.uid() or to_user = auth.uid());

create function public.send_points(p_to uuid, p_amount integer) returns bigint
language plpgsql security definer set search_path = ''
as $$
declare
  v_from uuid := auth.uid();
  v_id bigint;
begin
  if v_from is null then
    raise exception 'not signed in';
  end if;
  if p_amount is null or p_amount <= 0 then
    raise exception 'amount must be positive';
  end if;
  if p_to is null or p_to = v_from then
    raise exception 'invalid recipient';
  end if;
  perform 1 from public.wallets w where w.user_id = p_to;
  if not found then
    raise exception 'recipient has no wallet';
  end if;
  update public.wallets set balance = balance - p_amount
  where user_id = v_from and balance >= p_amount;
  if not found then
    raise exception 'insufficient balance';
  end if;
  update public.wallets set balance = balance + p_amount where user_id = p_to;
  insert into public.transfers (from_user, to_user, amount)
  values (v_from, p_to, p_amount)
  returning id into v_id;
  return v_id;
end
$$;
