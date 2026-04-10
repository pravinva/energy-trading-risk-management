-- ============================================================================
-- APEX Energy Trading Platform - Risk Management Tables
-- ============================================================================
-- Creates tables for VaR calculations, risk limits, and exposure monitoring
-- ============================================================================

USE CATALOG apex_fresh;

-- ============================================================================
-- Risk Analytics
-- ============================================================================

CREATE TABLE IF NOT EXISTS apex_fresh.risk.var_results (
  run_id STRING NOT NULL COMMENT 'VaR calculation run identifier',
  market STRING NOT NULL COMMENT 'Market (NEM, EPEX, ERCOT)',
  exposure_mw DOUBLE COMMENT 'Net exposure in MW',
  var_95 DOUBLE COMMENT 'Value at Risk at 95% confidence level',
  var_99 DOUBLE COMMENT 'Value at Risk at 99% confidence level',
  expected_shortfall_95 DOUBLE COMMENT 'Expected Shortfall (CVaR) at 95%',
  calculated_at TIMESTAMP COMMENT 'Calculation timestamp'
)
USING DELTA
COMMENT 'Value at Risk and Expected Shortfall calculations';

CREATE TABLE IF NOT EXISTS apex_fresh.risk.limit_definitions (
  metric STRING NOT NULL COMMENT 'Risk metric name',
  limit_value DOUBLE COMMENT 'Limit threshold value'
)
USING DELTA
COMMENT 'Risk limit definitions and thresholds';
