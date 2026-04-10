-- ============================================================================
-- APEX Energy Trading Platform - Trading Tables
-- ============================================================================
-- Creates tables for trade capture, offer stacks, and dispatch
-- ============================================================================

USE CATALOG apex_fresh;

-- ============================================================================
-- Ingestion Layer (Raw ETRM data)
-- ============================================================================

CREATE TABLE IF NOT EXISTS apex_fresh.ingestion.raw_etrm_trades (
  source_system STRING NOT NULL COMMENT 'Source ETRM system identifier',
  market STRING NOT NULL COMMENT 'Market identifier (NEM, EPEX, ERCOT)',
  payload STRING COMMENT 'Raw JSON payload from ETRM system',
  processed BOOLEAN COMMENT 'Processing status flag',
  received_at TIMESTAMP COMMENT 'Ingestion timestamp'
)
USING DELTA
COMMENT 'Raw ETRM trade data landing zone for DLT processing';

-- ============================================================================
-- Trading Analytics Layer
-- ============================================================================

CREATE TABLE IF NOT EXISTS apex_fresh.trading.trades (
  trade_id STRING NOT NULL COMMENT 'Unique trade identifier',
  market STRING NOT NULL COMMENT 'Market (NEM, EPEX, ERCOT)',
  instrument_id STRING COMMENT 'Traded instrument identifier',
  trader_id STRING COMMENT 'Trader identifier',
  direction STRING COMMENT 'Trade direction (BUY, SELL)',
  volume_mw DECIMAL(10,2) COMMENT 'Trade volume in MW',
  price DECIMAL(12,4) COMMENT 'Trade price',
  source_system STRING COMMENT 'Source ETRM system',
  ingested_at TIMESTAMP COMMENT 'Processing timestamp'
)
USING DELTA
COMMENT 'Processed trade records from ETRM systems';

CREATE TABLE IF NOT EXISTS apex_fresh.trading.offer_stacks (
  asset_id STRING NOT NULL COMMENT 'Asset identifier',
  scenario STRING NOT NULL COMMENT 'Scenario name',
  created_at TIMESTAMP COMMENT 'Stack creation timestamp'
)
USING DELTA
COMMENT 'Offer stack definitions for dispatch optimization';

CREATE TABLE IF NOT EXISTS apex_fresh.trading.offer_bands (
  asset_id STRING NOT NULL COMMENT 'Asset identifier',
  scenario STRING NOT NULL COMMENT 'Scenario name',
  band_index INT NOT NULL COMMENT 'Band number in offer stack',
  price DOUBLE COMMENT 'Offer price for this band',
  volume_mw DOUBLE COMMENT 'Volume MW for this band',
  created_at TIMESTAMP COMMENT 'Band creation timestamp'
)
USING DELTA
COMMENT 'Individual price-volume bands within offer stacks';

CREATE TABLE IF NOT EXISTS apex_fresh.trading.dispatch_reference (
  market STRING NOT NULL COMMENT 'Market identifier',
  asset_id STRING NOT NULL COMMENT 'Asset identifier',
  service_type STRING COMMENT 'Service type (ENERGY, FCAS, ANCILLARY)'
)
USING DELTA
COMMENT 'Asset dispatch configuration and service mappings';
