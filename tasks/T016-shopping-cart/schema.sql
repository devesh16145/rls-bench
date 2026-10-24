create table public.products (
  id bigint primary key,
  name text not null,
  price numeric(10, 2) not null,
  is_active boolean not null default true
);

create table public.cart_items (
  user_id uuid not null default auth.uid() references auth.users(id),
  product_id bigint not null references public.products(id),
  quantity integer not null check (quantity > 0),
  primary key (user_id, product_id)
);
