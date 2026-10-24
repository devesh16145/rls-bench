create table public.orgs (
  id bigint primary key,
  name text not null
);

create table public.org_members (
  org_id bigint not null references public.orgs(id),
  user_id uuid not null references auth.users(id),
  role text not null check (role in ('admin', 'member')),
  primary key (org_id, user_id)
);

create table public.invites (
  token text primary key,
  org_id bigint not null references public.orgs(id),
  email text not null,
  role text not null check (role in ('admin', 'member')),
  expires_at timestamptz not null,
  accepted_at timestamptz,
  invited_by uuid not null references auth.users(id)
);
