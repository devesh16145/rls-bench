insert into auth.users (id, email) values
  ('00000000-0000-0000-0000-000000000001', 'rita@example.com'),
  ('00000000-0000-0000-0000-000000000002', 'abe@example.com'),
  ('00000000-0000-0000-0000-000000000003', 'bea@example.com');

insert into public.approvers (user_id, limit_amount) values ('00000000-0000-0000-0000-000000000002', 1000), ('00000000-0000-0000-0000-000000000003', 50000);

insert into public.purchase_orders (id, requester_id, vendor, amount) values
  (1, '00000000-0000-0000-0000-000000000001', 'Stationery Co', 500),
  (2, '00000000-0000-0000-0000-000000000001', 'Cloud hosting', 800),
  (3, '00000000-0000-0000-0000-000000000001', 'Laptops Ltd', 20000),
  (4, '00000000-0000-0000-0000-000000000003', 'Coffee beans', 300),
  (5, '00000000-0000-0000-0000-000000000001', 'Monitors Inc', 900);

insert into public.po_approvals (po_id, approver_id, decision) values (5, '00000000-0000-0000-0000-000000000002', 'approve');

select setval(pg_get_serial_sequence('public.purchase_orders', 'id'), 5);
