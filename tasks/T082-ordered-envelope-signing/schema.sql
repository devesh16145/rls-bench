create table public.envelopes (
  id bigint primary key,
  sender_id uuid not null references auth.users(id),
  title text not null,
  status text not null default 'sent' check (status in ('sent', 'completed', 'voided'))
);

create table public.envelope_recipients (
  envelope_id bigint not null references public.envelopes(id),
  user_id uuid not null references auth.users(id),
  sign_order integer not null,
  signed_at timestamptz,
  primary key (envelope_id, user_id),
  unique (envelope_id, sign_order)
);
