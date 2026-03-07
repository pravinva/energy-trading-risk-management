USE CATALOG apex_fresh;

DELETE FROM apex_fresh.risk.limit_definitions;
INSERT INTO apex_fresh.risk.limit_definitions (metric, limit_value) VALUES
  ('Gross MW', 5000.0),
  ('Intraday Drawdown', 50000.0);

DELETE FROM apex_fresh.portfolio.revenue_rates;
INSERT INTO apex_fresh.portfolio.revenue_rates (component, rate_value) VALUES
  ('Ancillary Services', 0.18),
  ('Capacity Daily Rate', 4.5),
  ('PPA Hedge Value', 0.12);

DELETE FROM apex_fresh.portfolio.simulation_defaults;
INSERT INTO apex_fresh.portfolio.simulation_defaults (
  market,
  duration_hours_default,
  duration_hours_max,
  ancillary_pct_default,
  ancillary_pct_max,
  ppa_mw_default,
  ppa_mw_max,
  ppa_mtm_factor
) VALUES
  ('NEM', 2, 8, 40, 100, 50, 300, 0.8),
  ('EPEX', 2, 8, 35, 100, 45, 300, 0.8),
  ('ERCOT', 2, 8, 45, 100, 60, 350, 0.8);

DELETE FROM apex_fresh.analytics.strategy_catalog;
INSERT INTO apex_fresh.analytics.strategy_catalog (market, strategy, available) VALUES
  ('NEM', 'Simple Momentum', true),
  ('NEM', 'Mean Reversion', true),
  ('NEM', 'FCAS Spike', true),
  ('EPEX', 'Simple Momentum', true),
  ('EPEX', 'Mean Reversion', true),
  ('EPEX', 'FCAS Spike', false),
  ('ERCOT', 'Simple Momentum', true),
  ('ERCOT', 'Mean Reversion', true),
  ('ERCOT', 'FCAS Spike', true);

DELETE FROM apex_fresh.trading.dispatch_reference;
INSERT INTO apex_fresh.trading.dispatch_reference (market, asset_id, service_type) VALUES
  ('NEM', 'HORNSDALE_1', 'ENERGY'),
  ('NEM', 'HORNSDALE_1', 'RAISE 6S'),
  ('NEM', 'HORNSDALE_1', 'LOWER 6S'),
  ('NEM', 'WARATAH_1', 'ENERGY'),
  ('NEM', 'BOULDERCOMBE_1', 'ENERGY'),
  ('NEM', 'TORRENS_B_BESS', 'ENERGY'),
  ('EPEX', 'DE_BESS_1', 'ENERGY'),
  ('EPEX', 'DE_BESS_1', 'BALANCING_RESERVE'),
  ('EPEX', 'FR_BESS_1', 'ENERGY'),
  ('EPEX', 'NL_BESS_1', 'ENERGY'),
  ('ERCOT', 'TX_WEST_1', 'ENERGY'),
  ('ERCOT', 'TX_WEST_1', 'REG UP'),
  ('ERCOT', 'TX_WEST_1', 'REG DOWN'),
  ('ERCOT', 'TX_WEST_1', 'ECRS'),
  ('ERCOT', 'TX_WEST_2', 'ENERGY'),
  ('ERCOT', 'TX_HOUSTON_1', 'ENERGY'),
  ('ERCOT', 'TX_NORTH_1', 'ENERGY');
