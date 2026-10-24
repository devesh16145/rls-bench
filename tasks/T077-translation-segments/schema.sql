create table public.projects (
  id bigint primary key,
  name text not null
);

create table public.translators (
  project_id bigint not null references public.projects(id),
  user_id uuid not null references auth.users(id),
  lang text not null,
  role text not null check (role in ('translator', 'reviewer')),
  primary key (project_id, user_id, lang)
);

create table public.segments (
  id bigint primary key,
  project_id bigint not null references public.projects(id),
  lang text not null,
  source_text text not null,
  target_text text,
  status text not null default 'draft' check (status in ('draft', 'reviewed')),
  translated_by uuid references auth.users(id)
);
