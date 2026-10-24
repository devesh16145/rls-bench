create table public.documents (
  id bigint primary key,
  title text not null,
  body text not null default '',
  checked_out_by uuid references auth.users(id)
);

create table public.doc_access (
  doc_id bigint not null references public.documents(id),
  user_id uuid not null references auth.users(id),
  can_edit boolean not null default false,
  primary key (doc_id, user_id)
);
