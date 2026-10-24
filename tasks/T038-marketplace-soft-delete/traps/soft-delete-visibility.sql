create schema private;

grant usage on schema private to anon, authenticated;

create function private.is_moderator() returns boolean
language sql stable security definer set search_path = ''
as $$
  select exists (select 1 from public.moderators m where m.user_id = auth.uid())
$$;

create function private.listing_flagged(p_listing_id bigint) returns boolean
language sql stable security definer set search_path = ''
as $$
  select l.is_flagged from public.listings l where l.id = p_listing_id
$$;

alter table public.moderators enable row level security;
alter table public.listings enable row level security;

create policy listings_select on public.listings
  for select to anon, authenticated
  using (
    (status = 'active' and not is_flagged and deleted_at is null)
    or (seller_id = auth.uid() and deleted_at is null)
    or private.is_moderator()
  );

create policy listings_insert on public.listings
  for insert to authenticated
  with check (seller_id = auth.uid() and not is_flagged and deleted_at is null);

create policy listings_update on public.listings
  for update to authenticated
  using ((seller_id = auth.uid() and deleted_at is null) or private.is_moderator())
  with check (
    (seller_id = auth.uid() and is_flagged = private.listing_flagged(id))
    or private.is_moderator()
  );
