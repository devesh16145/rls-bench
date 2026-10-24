create table public.profiles (
  user_id uuid primary key default auth.uid() references auth.users(id),
  display_name text not null,
  bio text not null default '',
  visibility text not null default 'members' check (visibility in ('public', 'members', 'private'))
);
