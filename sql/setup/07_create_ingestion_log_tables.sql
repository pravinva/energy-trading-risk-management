-- ============================================================================
-- APEX Energy Trading Platform - Ingestion Log Tables
-- ============================================================================
-- Creates logging tables for tracking data ingestion from external APIs
-- ============================================================================

USE CATALOG apex_fresh;

-- ============================================================================
-- NEMWEB Ingestion Logs
-- ============================================================================

CREATE SCHEMA IF NOT EXISTS apex_fresh.nemweb
  COMMENT 'NEMWEB-specific data and ingestion logs';

CREATE TABLE IF NOT EXISTS apex_fresh.nemweb.ingestion_log (
  log_id STRING NOT NULL COMMENT 'Unique log entry identifier',
  data_type STRING NOT NULL COMMENT 'Type of data ingested (DISPATCH_PRICES, PREDISPATCH, DEMAND)',
  date_loaded DATE NOT NULL COMMENT 'Date of data being loaded',
  region_id STRING COMMENT 'NEM region identifier',
  records_loaded BIGINT COMMENT 'Number of records successfully loaded',
  records_failed BIGINT COMMENT 'Number of records that failed validation',
  start_timestamp TIMESTAMP COMMENT 'Ingestion start time',
  end_timestamp TIMESTAMP COMMENT 'Ingestion completion time',
  duration_seconds DOUBLE COMMENT 'Total ingestion duration in seconds',
  status STRING COMMENT 'Ingestion status (SUCCESS, FAILED, PARTIAL)',
  error_message STRING COMMENT 'Error message if status is FAILED'
)
USING DELTA
COMMENT 'NEMWEB data ingestion audit log';

-- ============================================================================
-- EPEX Ingestion Logs
-- ============================================================================

CREATE SCHEMA IF NOT EXISTS apex_fresh.epex
  COMMENT 'EPEX-specific data and ingestion logs';

CREATE TABLE IF NOT EXISTS apex_fresh.epex.ingestion_log (
  log_id STRING NOT NULL COMMENT 'Unique log entry identifier',
  market STRING NOT NULL COMMENT 'Market identifier (EPEX)',
  data_type STRING NOT NULL COMMENT 'Type of data (DAY_AHEAD_PRICES, INTRADAY_PRICES)',
  date_loaded DATE NOT NULL COMMENT 'Date of data being loaded',
  market_area STRING COMMENT 'Market area code (DE, FR, NL, BE, AT)',
  records_loaded BIGINT COMMENT 'Number of records successfully loaded',
  records_failed BIGINT COMMENT 'Number of records that failed validation',
  start_timestamp TIMESTAMP COMMENT 'Ingestion start time',
  status STRING COMMENT 'Ingestion status (SUCCESS, FAILED, PARTIAL)',
  duration_seconds DOUBLE COMMENT 'Total ingestion duration in seconds',
  error_message STRING COMMENT 'Error message if status is FAILED'
)
USING DELTA
COMMENT 'EPEX data ingestion audit log';

-- ============================================================================
-- ERCOT Ingestion Logs
-- ============================================================================

CREATE SCHEMA IF NOT EXISTS apex_fresh.ercot
  COMMENT 'ERCOT-specific data and ingestion logs';

CREATE TABLE IF NOT EXISTS apex_fresh.ercot.ingestion_log (
  log_id STRING NOT NULL COMMENT 'Unique log entry identifier',
  market STRING NOT NULL COMMENT 'Market identifier (ERCOT)',
  data_type STRING NOT NULL COMMENT 'Type of data (REAL_TIME_PRICES, DAY_AHEAD_PRICES)',
  date_loaded DATE NOT NULL COMMENT 'Date of data being loaded',
  settlement_point STRING COMMENT 'Settlement point node ID',
  records_loaded BIGINT COMMENT 'Number of records successfully loaded',
  records_failed BIGINT COMMENT 'Number of records that failed validation',
  start_timestamp TIMESTAMP COMMENT 'Ingestion start time',
  status STRING COMMENT 'Ingestion status (SUCCESS, FAILED, PARTIAL)',
  duration_seconds DOUBLE COMMENT 'Total ingestion duration in seconds',
  error_message STRING COMMENT 'Error message if status is FAILED'
)
USING DELTA
COMMENT 'ERCOT data ingestion audit log';
