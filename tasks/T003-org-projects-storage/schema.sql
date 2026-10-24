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

create table public.projects (
  id bigint primary key,
  org_id bigint not null references public.orgs(id),
  name text not null
);

create index org_members_user_id_idx on public.org_members (user_id);
create index projects_org_id_idx on public.projects (org_id);
