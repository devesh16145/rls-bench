insert into auth.users (id, email) values
  ('00000000-0000-0000-0000-000000000001', 'olga@example.com'),
  ('00000000-0000-0000-0000-000000000002', 'sid@example.com'),
  ('00000000-0000-0000-0000-000000000003', 'tara@example.com'),
  ('00000000-0000-0000-0000-000000000004', 'ugo@example.com');

insert into public.contracts (id, owner_id, title) values
  (1, '00000000-0000-0000-0000-000000000001', 'NDA with Acme'),
  (2, '00000000-0000-0000-0000-000000000001', 'Office lease draft'),
  (3, '00000000-0000-0000-0000-000000000003', 'Supplier MSA');

insert into public.contract_shares (contract_id, user_id) values (1, '00000000-0000-0000-0000-000000000002');

insert into public.contract_versions (id, contract_id, version, body, created_by) values
  (1, 1, 1, 'Initial draft', '00000000-0000-0000-0000-000000000001'),
  (2, 1, 2, 'Redlines from legal', '00000000-0000-0000-0000-000000000002'),
  (3, 2, 1, 'Lease v1', '00000000-0000-0000-0000-000000000001'),
  (4, 3, 1, 'MSA v1', '00000000-0000-0000-0000-000000000003');

insert into public.contract_tags (contract_id, tag) values (1, 'nda'), (2, 'real-estate'), (3, 'supplier');

select setval(pg_get_serial_sequence('public.contract_versions', 'id'), 4);
