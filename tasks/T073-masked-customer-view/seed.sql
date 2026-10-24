insert into auth.users (id, email) values
  ('00000000-0000-0000-0000-000000000001', 'ag_n@example.com'),
  ('00000000-0000-0000-0000-000000000002', 'ag_s@example.com'),
  ('00000000-0000-0000-0000-000000000003', 'sup@example.com'),
  ('00000000-0000-0000-0000-000000000004', 'usr@example.com');

insert into public.support_agents (user_id, region) values ('00000000-0000-0000-0000-000000000001', 'north'), ('00000000-0000-0000-0000-000000000002', 'south');

insert into public.supervisors (user_id) values ('00000000-0000-0000-0000-000000000003');

insert into public.customers (id, region, full_name, email, phone) values
  (1, 'north', 'Asha Rao', 'asha@example.com', '9876543210'),
  (2, 'north', 'Bilal Khan', 'bilal@mail.in', '9123456780'),
  (3, 'south', 'Chitra Nair', 'chitra@example.org', '9988776655');
