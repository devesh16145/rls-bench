create schema private;

grant usage on schema private to authenticated;

create function private.campaign_active(p_campaign_id bigint) returns boolean
language sql stable security definer set search_path = ''
as $$
  select exists (select 1 from public.campaigns c where c.id = p_campaign_id and c.status = 'active')
$$;

alter table public.campaigns enable row level security;
alter table public.donations enable row level security;

revoke update on public.campaigns from anon, authenticated;
grant update (status) on public.campaigns to authenticated;

create policy campaigns_select on public.campaigns
  for select to authenticated
  using (true);

create policy campaigns_insert on public.campaigns
  for insert to authenticated
  with check (owner_id = auth.uid() and status = 'active');

create policy campaigns_update on public.campaigns
  for update to authenticated
  using (owner_id = auth.uid())
  with check (owner_id = auth.uid());

create policy donations_select on public.donations
  for select to authenticated
  using (donor_id = auth.uid());

create policy donations_insert on public.donations
  for insert to authenticated
  with check (donor_id = auth.uid() and amount_cents > 0 and private.campaign_active(campaign_id));

create view public.campaign_donations as
select
  d.id,
  d.campaign_id,
  d.amount_cents,
  d.message,
  d.anonymous,
  d.donor_id
from public.donations d
join public.campaigns c on c.id = d.campaign_id
where c.owner_id = auth.uid() or d.donor_id = auth.uid();

revoke all on public.campaign_donations from anon;
grant select on public.campaign_donations to authenticated;
