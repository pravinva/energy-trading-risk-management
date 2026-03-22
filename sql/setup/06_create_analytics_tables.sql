-- ============================================================================
-- APEX Energy Trading Platform - Analytics Tables
-- ============================================================================
-- Creates tables for ML models, forecasts, backtests, and model lineage
-- ============================================================================

USE CATALOG apex_fresh;

-- ============================================================================
-- Analytics and ML
-- ============================================================================

CREATE TABLE IF NOT EXISTS apex_fresh.analytics.model_performance (
  model_name STRING NOT NULL COMMENT 'ML model identifier',
  market STRING NOT NULL COMMENT 'Market (NEM, EPEX, ERCOT)',
  mape DOUBLE COMMENT 'Mean Absolute Percentage Error',
  rmse DOUBLE COMMENT 'Root Mean Squared Error',
  r2 DOUBLE COMMENT 'R-squared coefficient of determination',
  run_timestamp TIMESTAMP COMMENT 'Model run timestamp'
)
USING DELTA
COMMENT 'ML model performance metrics and evaluation results';

CREATE TABLE IF NOT EXISTS apex_fresh.analytics.backtest_runs (
  strategy STRING NOT NULL COMMENT 'Trading strategy identifier',
  market STRING NOT NULL COMMENT 'Market (NEM, EPEX, ERCOT)',
  trades BIGINT COMMENT 'Number of trades executed in backtest',
  win_rate DOUBLE COMMENT 'Win rate percentage (0-1)',
  total_pnl DOUBLE COMMENT 'Total P&L from backtest',
  sharpe DOUBLE COMMENT 'Sharpe ratio',
  run_timestamp TIMESTAMP COMMENT 'Backtest run timestamp'
)
USING DELTA
COMMENT 'Strategy backtest results and performance metrics';

CREATE TABLE IF NOT EXISTS apex_fresh.analytics.price_forecasts (
  market STRING NOT NULL COMMENT 'Market (NEM, EPEX, ERCOT)',
  instrument STRING NOT NULL COMMENT 'Instrument identifier',
  forecast_datetime TIMESTAMP NOT NULL COMMENT 'Forecast target datetime',
  forecast_price DOUBLE COMMENT 'Predicted price',
  forecast_demand_mw DOUBLE COMMENT 'Predicted demand in MW',
  model_name STRING COMMENT 'ML model used for forecast',
  run_timestamp TIMESTAMP COMMENT 'Forecast generation timestamp'
)
USING DELTA
COMMENT 'Price and demand forecasts from ML models';

CREATE TABLE IF NOT EXISTS apex_fresh.analytics.model_lineage (
  market STRING NOT NULL COMMENT 'Market (NEM, EPEX, ERCOT)',
  model_name STRING NOT NULL COMMENT 'ML model identifier',
  run_timestamp TIMESTAMP NOT NULL COMMENT 'Model run timestamp',
  training_start_utc TIMESTAMP COMMENT 'Training data start timestamp',
  training_end_utc TIMESTAMP COMMENT 'Training data end timestamp',
  feature_set STRING COMMENT 'Feature set description',
  feature_hash STRING COMMENT 'Feature set hash for reproducibility'
)
USING DELTA
COMMENT 'ML model training lineage and reproducibility tracking';

CREATE TABLE IF NOT EXISTS apex_fresh.analytics.strategy_catalog (
  market STRING NOT NULL COMMENT 'Market (NEM, EPEX, ERCOT)',
  strategy STRING NOT NULL COMMENT 'Strategy name',
  available BOOLEAN COMMENT 'Strategy availability flag'
)
USING DELTA
COMMENT 'Available trading strategies per market';
