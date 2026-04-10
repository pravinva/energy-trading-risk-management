-- ============================================================================
-- APEX Energy Trading Platform - Market Data Tables
-- ============================================================================
-- Creates price and market data tables for NEM, EPEX, and ERCOT markets
-- ============================================================================

USE CATALOG apex_fresh;

-- ============================================================================
-- NEM (Australian National Electricity Market) Tables
-- ============================================================================

CREATE TABLE IF NOT EXISTS apex_fresh.market_nem.prices (
  interval_datetime TIMESTAMP NOT NULL COMMENT 'Trading interval timestamp (5-minute intervals)',
  region_id STRING NOT NULL COMMENT 'NEM region (NSW1, QLD1, SA1, TAS1, VIC1)',
  rrp DECIMAL(12,4) COMMENT 'Regional Reference Price (AUD/MWh)',
  data_source STRING COMMENT 'Data source identifier (NEMWEB, API, etc.)'
)
USING DELTA
COMMENT 'NEM spot prices by region and interval';

-- ============================================================================
-- EPEX SPOT (European Power Exchange) Tables
-- ============================================================================

CREATE TABLE IF NOT EXISTS apex_fresh.market_epex.prices (
  delivery_datetime TIMESTAMP NOT NULL COMMENT 'Power delivery start time',
  bidding_zone STRING NOT NULL COMMENT 'EPEX bidding zone (DE-LU, FR, etc.)',
  price_eur_mwh DECIMAL(12,4) COMMENT 'Day-ahead auction price (EUR/MWh)',
  mtu_minutes INT COMMENT 'Market Time Unit duration in minutes (15, 60)',
  data_source STRING COMMENT 'Data source identifier'
)
USING DELTA
COMMENT 'EPEX SPOT day-ahead and intraday prices';

-- ============================================================================
-- ERCOT (Electric Reliability Council of Texas) Tables
-- ============================================================================

CREATE TABLE IF NOT EXISTS apex_fresh.market_ercot.lmp (
  interval_datetime TIMESTAMP NOT NULL COMMENT 'Market interval timestamp',
  node_id STRING NOT NULL COMMENT 'ERCOT settlement point node ID',
  lmp DECIMAL(12,4) COMMENT 'Locational Marginal Price (USD/MWh)',
  rtcb_signal DECIMAL(12,4) COMMENT 'Real-Time Co-optimization of Balancing signal',
  data_source STRING COMMENT 'Data source identifier'
)
USING DELTA
COMMENT 'ERCOT nodal LMP and RTCB dispatch signals';
