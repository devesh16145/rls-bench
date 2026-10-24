create table public.incidents (
  id bigint primary key,
  title text not null,
  severity text not null check (severity in ('minor', 'major')),
  status text not null default 'investigating' check (status in ('investigating', 'resolved')),
  is_published boolean not null default false
);

create table public.incident_updates (
  id bigint primary key,
  incident_id bigint not null references public.incidents(id) on delete cascade,
  body text not null,
  is_published boolean not null default false
);
