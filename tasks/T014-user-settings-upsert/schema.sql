create table public.user_settings (
  user_id uuid primary key default auth.uid() references auth.users(id),
  timezone text not null default 'UTC',
  weekly_goal integer not null default 3 check (weekly_goal > 0),
  reminders_enabled boolean not null default true
);
