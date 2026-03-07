USE CATALOG apex_fresh;

CREATE SCHEMA IF NOT EXISTS apex_fresh.market_nem;
CREATE SCHEMA IF NOT EXISTS apex_fresh.market_epex;
CREATE SCHEMA IF NOT EXISTS apex_fresh.market_ercot;
CREATE SCHEMA IF NOT EXISTS apex_fresh.trading;
CREATE SCHEMA IF NOT EXISTS apex_fresh.ingestion;

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

