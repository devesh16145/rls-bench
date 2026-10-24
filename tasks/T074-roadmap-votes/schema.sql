create table public.roadmap_items (
  id bigint primary key,
  title text not null,
  status text not null default 'planned' check (status in ('planned', 'in_progress', 'shipped'))
);

create table public.item_votes (
  user_id uuid not null default auth.uid() references auth.users(id),
  item_id bigint not null references public.roadmap_items(id),
  primary key (user_id, item_id)
);
