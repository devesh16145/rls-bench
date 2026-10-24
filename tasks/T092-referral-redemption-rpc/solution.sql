alter table public.referral_codes enable row level security;
alter table public.referrals enable row level security;
alter table public.credits enable row level security;

create policy referral_codes_select on public.referral_codes
  for select to authenticated
  using (user_id = auth.uid());

create policy referrals_select on public.referrals
  for select to authenticated
  using (referrer_id = auth.uid() or referee_id = auth.uid());

create policy credits_select on public.credits
  for select to authenticated
  using (user_id = auth.uid());

create function public.redeem_referral(p_code text) returns bigint
language plpgsql security definer set search_path = ''
as $$
declare
  v_uid uuid := auth.uid();
  v_referrer uuid;
  v_id bigint;
begin
  if v_uid is null then
    raise exception 'not signed in';
  end if;
  select c.user_id into v_referrer from public.referral_codes c where c.code = p_code;
  if not found then
    raise exception 'unknown referral code';
  end if;
  if v_referrer = v_uid then
    raise exception 'cannot use your own referral code';
  end if;
  if exists (select 1 from public.referrals r where r.referee_id = v_uid) then
    raise exception 'you have already used a referral code';
  end if;
  if (select count(*) from public.referrals r where r.referrer_id = v_referrer) >= 5 then
    raise exception 'this referral code has reached its limit';
  end if;
  insert into public.referrals (referrer_id, referee_id) values (v_referrer, v_uid) returning id into v_id;
  insert into public.credits (user_id, amount, reason) values
    (v_uid, 100, 'referred'),
    (v_referrer, 100, 'referral bonus');
  return v_id;
end
$$;
