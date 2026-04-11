-- ============================================================================
-- APEX Energy Trading Platform - Portfolio Tables
-- ============================================================================
-- Creates tables for PPA book, revenue stacking, and portfolio analytics
-- ============================================================================

USE CATALOG apex_fresh;

-- ============================================================================
-- Portfolio Management
-- ============================================================================

CREATE TABLE IF NOT EXISTS apex_fresh.portfolio.ppa_book (
  ppa_id STRING NOT NULL COMMENT 'Power Purchase Agreement unique identifier',
  market STRING NOT NULL COMMENT 'Market (NEM, EPEX, ERCOT)',
  counterparty STRING COMMENT 'PPA counterparty name',
  volume_mw DOUBLE COMMENT 'Contracted volume in MW',
  strike_price DOUBLE COMMENT 'PPA strike price',
  tenor_years INT COMMENT 'Contract duration in years',
  as_of_timestamp TIMESTAMP COMMENT 'Record as-of timestamp'
)
USING DELTA
COMMENT 'Power Purchase Agreement portfolio book';

CREATE TABLE IF NOT EXISTS apex_fresh.portfolio.revenue_rates (
  component STRING NOT NULL COMMENT 'Revenue component (ENERGY, FCAS, ANCILLARY)',
  rate_value DOUBLE COMMENT 'Rate or percentage value'
)
USING DELTA
COMMENT 'Revenue stacking component rates and percentages';

CREATE TABLE IF NOT EXISTS apex_fresh.portfolio.simulation_defaults (
  market STRING NOT NULL COMMENT 'Market identifier',
  duration_hours_default INT COMMENT 'Default simulation duration in hours',
  duration_hours_max INT COMMENT 'Maximum simulation duration in hours',
  ancillary_pct_default INT COMMENT 'Default ancillary service percentage',
  ancillary_pct_max INT COMMENT 'Maximum ancillary service percentage',
  ppa_mw_default INT COMMENT 'Default PPA volume MW',
  ppa_mw_max INT COMMENT 'Maximum PPA volume MW',
  ppa_mtm_factor DOUBLE COMMENT 'PPA mark-to-market adjustment factor'
)
USING DELTA
COMMENT 'Market-specific simulation parameter defaults and limits';

-- ============================================================================
-- Reference Defaults (idempotent seeds)
-- ============================================================================

INSERT INTO apex_fresh.portfolio.revenue_rates
SELECT 'Ancillary Services', 0.18
WHERE NOT EXISTS (
  SELECT 1 FROM apex_fresh.portfolio.revenue_rates
  WHERE component = 'Ancillary Services'
);

INSERT INTO apex_fresh.portfolio.revenue_rates
SELECT 'Capacity Daily Rate', 4.5
WHERE NOT EXISTS (
  SELECT 1 FROM apex_fresh.portfolio.revenue_rates
  WHERE component = 'Capacity Daily Rate'
);

INSERT INTO apex_fresh.portfolio.revenue_rates
SELECT 'PPA Hedge Value', 0.12
WHERE NOT EXISTS (
  SELECT 1 FROM apex_fresh.portfolio.revenue_rates
  WHERE component = 'PPA Hedge Value'
);

INSERT INTO apex_fresh.portfolio.simulation_defaults
SELECT 'NEM', 2, 8, 40, 100, 50, 300, 0.8
WHERE NOT EXISTS (
  SELECT 1 FROM apex_fresh.portfolio.simulation_defaults
  WHERE upper(market) = 'NEM'
);

INSERT INTO apex_fresh.portfolio.simulation_defaults
SELECT 'EPEX', 2, 8, 35, 100, 45, 300, 0.8
WHERE NOT EXISTS (
  SELECT 1 FROM apex_fresh.portfolio.simulation_defaults
  WHERE upper(market) = 'EPEX'
);

INSERT INTO apex_fresh.portfolio.simulation_defaults
SELECT 'ERCOT', 2, 8, 45, 100, 60, 350, 0.8
WHERE NOT EXISTS (
  SELECT 1 FROM apex_fresh.portfolio.simulation_defaults
  WHERE upper(market) = 'ERCOT'
);
