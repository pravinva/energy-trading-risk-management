USE CATALOG apex_fresh;

CREATE SCHEMA IF NOT EXISTS apex_fresh.market_nem;
CREATE SCHEMA IF NOT EXISTS apex_fresh.market_epex;
CREATE SCHEMA IF NOT EXISTS apex_fresh.market_ercot;
CREATE SCHEMA IF NOT EXISTS apex_fresh.trading;
CREATE SCHEMA IF NOT EXISTS apex_fresh.ingestion;
CREATE SCHEMA IF NOT EXISTS apex_fresh.risk;
CREATE SCHEMA IF NOT EXISTS apex_fresh.portfolio;
CREATE SCHEMA IF NOT EXISTS apex_fresh.analytics;

CREATE TABLE IF NOT EXISTS apex_fresh.market_nem.prices (
  interval_datetime TIMESTAMP,
  region_id STRING,
  rrp DECIMAL(12,4),
  data_source STRING
);

CREATE TABLE IF NOT EXISTS apex_fresh.market_epex.prices (
  delivery_datetime TIMESTAMP,
  bidding_zone STRING,
  price_eur_mwh DECIMAL(12,4),
  mtu_minutes INT,
  data_source STRING
);

CREATE TABLE IF NOT EXISTS apex_fresh.market_ercot.lmp (
  interval_datetime TIMESTAMP,
  node_id STRING,
  lmp DECIMAL(12,4),
  rtcb_signal DECIMAL(12,4),
  data_source STRING
);

CREATE TABLE IF NOT EXISTS apex_fresh.ingestion.raw_etrm_trades (
  source_system STRING,
  market STRING,
  payload STRING,
  processed BOOLEAN,
  received_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS apex_fresh.trading.trades (
  trade_id STRING,
  market STRING,
  instrument_id STRING,
  trader_id STRING,
  direction STRING,
  volume_mw DECIMAL(10,2),
  price DECIMAL(12,4),
  source_system STRING,
  ingested_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS apex_fresh.trading.offer_stacks (
  asset_id STRING,
  scenario STRING,
  created_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS apex_fresh.trading.offer_bands (
  asset_id STRING,
  scenario STRING,
  band_index INT,
  price DOUBLE,
  volume_mw DOUBLE,
  created_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS apex_fresh.trading.dispatch_reference (
  market STRING,
  asset_id STRING,
  service_type STRING
);

CREATE TABLE IF NOT EXISTS apex_fresh.risk.var_results (
  run_id STRING,
  market STRING,
  exposure_mw DOUBLE,
  var_95 DOUBLE,
  var_99 DOUBLE,
  expected_shortfall_95 DOUBLE,
  calculated_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS apex_fresh.risk.limit_definitions (
  metric STRING,
  limit_value DOUBLE
);

CREATE TABLE IF NOT EXISTS apex_fresh.portfolio.ppa_book (
  ppa_id STRING,
  market STRING,
  counterparty STRING,
  volume_mw DOUBLE,
  strike_price DOUBLE,
  tenor_years INT,
  as_of_timestamp TIMESTAMP
);

CREATE TABLE IF NOT EXISTS apex_fresh.portfolio.revenue_rates (
  component STRING,
  rate_value DOUBLE
);

CREATE TABLE IF NOT EXISTS apex_fresh.portfolio.simulation_defaults (
  market STRING,
  duration_hours_default INT,
  duration_hours_max INT,
  ancillary_pct_default INT,
  ancillary_pct_max INT,
  ppa_mw_default INT,
  ppa_mw_max INT,
  ppa_mtm_factor DOUBLE
);

CREATE TABLE IF NOT EXISTS apex_fresh.analytics.model_performance (
  model_name STRING,
  market STRING,
  mape DOUBLE,
  rmse DOUBLE,
  r2 DOUBLE,
  run_timestamp TIMESTAMP
);

CREATE TABLE IF NOT EXISTS apex_fresh.analytics.backtest_runs (
  strategy STRING,
  market STRING,
  trades BIGINT,
  win_rate DOUBLE,
  total_pnl DOUBLE,
  sharpe DOUBLE,
  run_timestamp TIMESTAMP
);

CREATE TABLE IF NOT EXISTS apex_fresh.analytics.price_forecasts (
  market STRING,
  instrument STRING,
  forecast_datetime TIMESTAMP,
  forecast_price DOUBLE,
  forecast_demand_mw DOUBLE,
  model_name STRING,
  run_timestamp TIMESTAMP
);

CREATE TABLE IF NOT EXISTS apex_fresh.analytics.model_lineage (
  market STRING,
  model_name STRING,
  run_timestamp TIMESTAMP,
  training_start_utc TIMESTAMP,
  training_end_utc TIMESTAMP,
  feature_set STRING,
  feature_hash STRING
);

CREATE TABLE IF NOT EXISTS apex_fresh.analytics.strategy_catalog (
  market STRING,
  strategy STRING,
  available BOOLEAN
);

