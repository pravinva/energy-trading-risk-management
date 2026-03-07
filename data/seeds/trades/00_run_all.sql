INSERT INTO apex.portfolio.ppa_book VALUES
  ('PPA-001', 'IndustrialCo', 65.0, 84.0, 7),
  ('PPA-002', 'CloudWorks', 42.0, 91.5, 10),
  ('PPA-003', 'TransitGrid', 28.0, 88.0, 5);

INSERT INTO apex.reference.counterparties VALUES
  ('CP-001', 'GridRetail', 'BBB+', 'AU'),
  ('CP-002', 'North Hydro', 'A-', 'AU'),
  ('CP-003', 'CloudWorks', 'A', 'US');

INSERT INTO apex.market.forward_curves VALUES
  (current_date(), 'NSW', 'M+1', 89.5),
  (current_date(), 'NSW', 'Q+1', 92.8),
  (current_date(), 'ERCOT_HOUSTON', 'M+1', 72.1),
  (current_date(), 'DE-LU', 'M+1', 76.4);
