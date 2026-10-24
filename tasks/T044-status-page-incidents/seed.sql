insert into auth.users (id, email) values
  ('00000000-0000-0000-0000-000000000001', 'ana@example.com');

insert into public.incidents (id, title, severity, status, is_published) values
  (1, 'API latency in ap-south-1', 'major', 'resolved', true),
  (2, 'Suspected credential leak', 'major', 'investigating', false);

insert into public.incident_updates (id, incident_id, body, is_published) values
  (1, 1, 'Mitigated by scaling read replicas.', true),
  (2, 1, 'Internal note: root cause was a bad deploy.', false),
  (3, 2, 'We are rotating all API keys.', true);
