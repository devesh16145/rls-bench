insert into auth.users (id, email) values
  ('00000000-0000-0000-0000-000000000001', 'ana@example.com'),
  ('00000000-0000-0000-0000-000000000002', 'ben@example.com'),
  ('00000000-0000-0000-0000-000000000003', 'cy@example.com'),
  ('00000000-0000-0000-0000-000000000004', 'dee@example.com'),
  ('00000000-0000-0000-0000-000000000005', 'eli@example.com');

insert into public.employees (id, user_id, full_name, department, salary) values
  (1, '00000000-0000-0000-0000-000000000001', 'Ana Alves', 'HR', 95000),
  (2, '00000000-0000-0000-0000-000000000002', 'Ben Brooks', 'Engineering', 85000),
  (3, '00000000-0000-0000-0000-000000000003', 'Cy Chen', 'Engineering', 80000),
  (4, '00000000-0000-0000-0000-000000000004', 'Dee Diaz', 'Sales', 70000);
