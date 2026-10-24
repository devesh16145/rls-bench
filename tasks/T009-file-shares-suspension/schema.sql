create table public.accounts (
  user_id uuid primary key references auth.users(id),
  suspended boolean not null default false
);

create table public.files (
  id bigint primary key,
  owner_id uuid not null references auth.users(id),
  name text not null
);

create table public.file_shares (
  file_id bigint not null references public.files(id) on delete cascade,
  shared_with uuid not null references auth.users(id),
  can_edit boolean not null default false,
  expires_at timestamptz,
  primary key (file_id, shared_with)
);

create index files_owner_id_idx on public.files (owner_id);
create index file_shares_shared_with_idx on public.file_shares (shared_with);
