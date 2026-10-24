create table public.products (
  id bigint primary key,
  name text not null
);

create table public.purchases (
  user_id uuid not null references auth.users(id),
  product_id bigint not null references public.products(id),
  primary key (user_id, product_id)
);

create table public.reviews (
  product_id bigint not null references public.products(id),
  user_id uuid not null default auth.uid() references auth.users(id),
  rating integer not null check (rating between 1 and 5),
  body text not null default '',
  is_featured boolean not null default false,
  primary key (product_id, user_id)
);
