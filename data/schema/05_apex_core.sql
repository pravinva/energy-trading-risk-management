CREATE CATALOG IF NOT EXISTS apex;
USE CATALOG apex;

CREATE SCHEMA IF NOT EXISTS reference;
CREATE SCHEMA IF NOT EXISTS market;
CREATE SCHEMA IF NOT EXISTS trading;
CREATE SCHEMA IF NOT EXISTS risk;
CREATE SCHEMA IF NOT EXISTS portfolio;
CREATE SCHEMA IF NOT EXISTS analytics;

CREATE TABLE IF NOT EXISTS apex.reference.counterparties (
  counterparty_id STRING,
  counterparty_name STRING,
  credit_rating STRING,
  country STRING
);

CREATE TABLE IF NOT EXISTS apex.market.forward_curves (
  valuation_date DATE,
  hub STRING,
  tenor STRING,
  forward_price DOUBLE
);

CREATE TABLE IF NOT EXISTS apex.trading.trades (
  trade_id STRING,
  trader STRING,
  instrument STRING,
  side STRING,
  volume_mw DOUBLE,
  price DOUBLE,
  counterparty STRING,
  trade_time TIMESTAMP
);

CREATE TABLE IF NOT EXISTS apex.risk.var_results (
  run_id STRING,
  exposure_mw DOUBLE,
  var_95 DOUBLE,
  var_99 DOUBLE,
  expected_shortfall_95 DOUBLE,
  calculated_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS apex.portfolio.ppa_book (
  ppa_id STRING,
  counterparty STRING,
  volume_mw DOUBLE,
  strike_price DOUBLE,
  tenor_years INT
);

CREATE TABLE IF NOT EXISTS apex.analytics.model_performance (
  model_name STRING,
  mape DOUBLE,
  rmse DOUBLE,
  r2 DOUBLE,
  run_timestamp TIMESTAMP
);
