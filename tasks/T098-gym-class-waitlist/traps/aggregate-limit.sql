create schema private;

grant usage on schema private to authenticated;

create function private.is_instructor(p_class_id bigint) returns boolean
language sql stable security definer set search_path = ''
as $$
  select exists (select 1 from public.classes c where c.id = p_class_id and c.instructor_id = auth.uid())
$$;

create function private.has_room(p_class_id bigint) returns boolean
language sql stable security definer set search_path = ''
as $$
  select (select count(*) from public.class_spots s where s.class_id = p_class_id and s.status = 'enrolled') < (select c.capacity from public.classes c where c.id = p_class_id)
$$;

alter table public.classes enable row level security;
alter table public.class_spots enable row level security;

revoke update on public.class_spots from anon, authenticated;
grant update (status) on public.class_spots to authenticated;

create policy classes_select on public.classes
  for select to authenticated
  using (true);

create policy spots_select on public.class_spots
  for select to authenticated
  using (user_id = auth.uid() or private.is_instructor(class_id));

create policy spots_insert on public.class_spots
  for insert to authenticated
  with check (user_id = auth.uid());

create policy spots_update on public.class_spots
  for update to authenticated
  using (user_id = auth.uid())
  with check (user_id = auth.uid() and (status = 'waitlisted' or private.has_room(class_id)));

create policy spots_delete on public.class_spots
  for delete to authenticated
  using (user_id = auth.uid() or private.is_instructor(class_id));
