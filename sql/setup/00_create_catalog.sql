-- ============================================================================
-- APEX Energy Trading Platform - Catalog Creation
-- ============================================================================
-- Creates the apex_fresh catalog for the APEX energy trading platform
-- This catalog houses all schemas for NEM, EPEX, ERCOT markets plus
-- trading, risk, portfolio, and analytics data
-- ============================================================================

CREATE CATALOG IF NOT EXISTS apex_fresh
  COMMENT 'APEX Energy Analytics Platform — NEM · EPEX · ERCOT';

USE CATALOG apex_fresh;
