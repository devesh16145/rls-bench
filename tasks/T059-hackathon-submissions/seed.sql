insert into auth.users (id, email) values
  ('00000000-0000-0000-0000-000000000001', 'al@example.com'),
  ('00000000-0000-0000-0000-000000000002', 'bo@example.com'),
  ('00000000-0000-0000-0000-000000000003', 'cy@example.com'),
  ('00000000-0000-0000-0000-000000000004', 'jj@example.com'),
  ('00000000-0000-0000-0000-000000000005', 'kk@example.com');

insert into public.events (id, name, deadline) values (1, 'HackPune', '2099-06-01'), (2, 'HackGoa', '2020-06-01');

insert into public.teams (id, event_id, name) values (1, 1, 'Alpha'), (2, 1, 'Beta'), (3, 2, 'Gamma');

insert into public.team_members (team_id, user_id) values
  (1, '00000000-0000-0000-0000-000000000001'), (1, '00000000-0000-0000-0000-000000000002'), (2, '00000000-0000-0000-0000-000000000003'), (3, '00000000-0000-0000-0000-000000000003');

insert into public.judges (event_id, user_id) values (1, '00000000-0000-0000-0000-000000000004'), (2, '00000000-0000-0000-0000-000000000005');

insert into public.submissions (team_id, repo_url) values
  (1, 'https://github.com/alpha/app'),
  (3, 'https://github.com/gamma/app');
