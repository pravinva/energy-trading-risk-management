-- ============================================================================
-- APEX Energy Trading Platform - Schema Creation
-- ============================================================================
-- Creates all schemas within the apex_fresh catalog
-- ============================================================================

USE CATALOG apex_fresh;

-- Market-specific schemas for price and market data
CREATE SCHEMA IF NOT EXISTS apex_fresh.market_nem
  COMMENT 'NEM (Australia) — spot prices, generation, FCAS, BESS telemetry';

CREATE SCHEMA IF NOT EXISTS apex_fresh.market_epex
  COMMENT 'EPEX (Europe) — day-ahead, intraday, EU ETS';

CREATE SCHEMA IF NOT EXISTS apex_fresh.market_ercot
  COMMENT 'ERCOT (Americas) — nodal LMP, RTC+B dispatch signals';

-- Shared operational schemas
CREATE SCHEMA IF NOT EXISTS apex_fresh.ingestion
  COMMENT 'ETRM raw landing zone and sync metadata — DLT source';

CREATE SCHEMA IF NOT EXISTS apex_fresh.trading
  COMMENT 'Trade analytics layer — populated by DLT from ETRM sources';

CREATE SCHEMA IF NOT EXISTS apex_fresh.risk
  COMMENT 'VaR, stress tests, credit exposure, limit monitoring';

CREATE SCHEMA IF NOT EXISTS apex_fresh.portfolio
  COMMENT 'Revenue stacking, PPA book, asset benchmarking';

CREATE SCHEMA IF NOT EXISTS apex_fresh.analytics
  COMMENT 'ML forecasts, backtest results, model metadata';
