-- ============================================================================
-- NEMWEB Data Ingestion Schema
-- Real-time and historical data from AEMO (Australian Energy Market Operator)
-- ============================================================================

-- Catalog: apex

-- ============================================================================
-- Dispatch Prices (5-minute intervals)
-- ============================================================================

CREATE TABLE IF NOT EXISTS apex.market_nem.dispatch_prices (
  dispatch_id STRING,
  interval_datetime TIMESTAMP,
  region_id STRING,
  rrp DOUBLE,  -- Regional Reference Price ($/MWh)
  rop DOUBLE,  -- Regional Override Price
  demand_mw DOUBLE,  -- Total demand in MW
  intervention INT,  -- 0 = normal, 1 = intervention
  raise_6sec_price DOUBLE,  -- FCAS prices
  raise_60sec_price DOUBLE,
  raise_5min_price DOUBLE,
  raise_reg_price DOUBLE,
  lower_6sec_price DOUBLE,
  lower_60sec_price DOUBLE,
  lower_5min_price DOUBLE,
  lower_reg_price DOUBLE,
  ingestion_timestamp TIMESTAMP,
  data_source STRING,  -- 'NEMWEB' or 'SIMULATED'
  CONSTRAINT pk_dispatch_prices PRIMARY KEY (dispatch_id)
) USING DELTA
PARTITIONED BY (DATE(interval_datetime), region_id);

-- Indexes for query performance
CREATE INDEX IF NOT EXISTS idx_dispatch_datetime
ON apex.market_nem.dispatch_prices (interval_datetime);

CREATE INDEX IF NOT EXISTS idx_dispatch_region
ON apex.market_nem.dispatch_prices (region_id, interval_datetime);

COMMENT ON TABLE apex.market_nem.dispatch_prices IS
'5-minute dispatch prices from NEMWEB - real-time market data';

-- ============================================================================
-- Pre-Dispatch Forecasts (5-minute intervals, up to 40 hours ahead)
-- ============================================================================

CREATE TABLE IF NOT EXISTS apex.market_nem.predispatch_forecasts (
  forecast_id STRING,
  predispatch_run_datetime TIMESTAMP,  -- When forecast was generated
  interval_datetime TIMESTAMP,  -- When forecasted interval starts
  region_id STRING,
  forecast_price DOUBLE,  -- Forecasted RRP
  forecast_demand_mw DOUBLE,
  forecast_horizon_minutes INT,  -- How far ahead (minutes)
  intervention INT,
  ingestion_timestamp TIMESTAMP,
  CONSTRAINT pk_predispatch PRIMARY KEY (forecast_id)
) USING DELTA
PARTITIONED BY (DATE(predispatch_run_datetime), region_id);

CREATE INDEX IF NOT EXISTS idx_predispatch_datetime
ON apex.market_nem.predispatch_forecasts (interval_datetime);

CREATE INDEX IF NOT EXISTS idx_predispatch_run
ON apex.market_nem.predispatch_forecasts (predispatch_run_datetime, region_id);

COMMENT ON TABLE apex.market_nem.predispatch_forecasts IS
'Pre-dispatch price forecasts from NEMWEB - 5-minute intervals up to 40 hours ahead';

-- ============================================================================
-- Trading Prices (30-minute intervals)
-- ============================================================================

CREATE TABLE IF NOT EXISTS apex.market_nem.trading_prices (
  trading_id STRING,
  interval_datetime TIMESTAMP,  -- 30-minute interval
  region_id STRING,
  rrp DOUBLE,  -- Trading price ($/MWh)
  demand_mw DOUBLE,
  intervention INT,
  ingestion_timestamp TIMESTAMP,
  CONSTRAINT pk_trading_prices PRIMARY KEY (trading_id)
) USING DELTA
PARTITIONED BY (DATE(interval_datetime), region_id);

CREATE INDEX IF NOT EXISTS idx_trading_datetime
ON apex.market_nem.trading_prices (interval_datetime);

COMMENT ON TABLE apex.market_nem.trading_prices IS
'30-minute trading prices from NEMWEB';

-- ============================================================================
-- Demand Actuals (5-minute intervals)
-- ============================================================================

CREATE TABLE IF NOT EXISTS apex.market_nem.demand_actual (
  demand_id STRING,
  interval_datetime TIMESTAMP,
  region_id STRING,
  total_demand_mw DOUBLE,
  operational_demand_mw DOUBLE,  -- Demand met by scheduled/semi-scheduled
  available_generation_mw DOUBLE,
  available_load_mw DOUBLE,
  semi_scheduled_generation_mw DOUBLE,
  rooftop_solar_mw DOUBLE,
  ingestion_timestamp TIMESTAMP,
  CONSTRAINT pk_demand_actual PRIMARY KEY (demand_id)
) USING DELTA
PARTITIONED BY (DATE(interval_datetime), region_id);

CREATE INDEX IF NOT EXISTS idx_demand_datetime
ON apex.market_nem.demand_actual (interval_datetime);

COMMENT ON TABLE apex.market_nem.demand_actual IS
'Actual demand data from NEMWEB - 5-minute intervals';

-- ============================================================================
-- Generation by Fuel Type (5-minute intervals)
-- ============================================================================

CREATE TABLE IF NOT EXISTS apex.market_nem.generation_fuel_type (
  generation_id STRING,
  interval_datetime TIMESTAMP,
  region_id STRING,
  fuel_type STRING,  -- 'COAL', 'GAS', 'HYDRO', 'WIND', 'SOLAR', 'BATTERY'
  generation_mw DOUBLE,
  capacity_mw DOUBLE,
  availability_percent DOUBLE,
  ingestion_timestamp TIMESTAMP,
  CONSTRAINT pk_generation PRIMARY KEY (generation_id)
) USING DELTA
PARTITIONED BY (DATE(interval_datetime), region_id, fuel_type);

CREATE INDEX IF NOT EXISTS idx_generation_datetime
ON apex.market_nem.generation_fuel_type (interval_datetime);

COMMENT ON TABLE apex.market_nem.generation_fuel_type IS
'Generation by fuel type from NEMWEB';

-- ============================================================================
-- Interconnector Flows
-- ============================================================================

CREATE TABLE IF NOT EXISTS apex.market_nem.interconnector_flows (
  flow_id STRING,
  interval_datetime TIMESTAMP,
  interconnector_id STRING,  -- 'NSW1-VIC1', 'VIC1-SA1', etc.
  from_region_id STRING,
  to_region_id STRING,
  mw_flow DOUBLE,  -- Positive = export, Negative = import
  metered_mw DOUBLE,
  limit_mw DOUBLE,
  ingestion_timestamp TIMESTAMP,
  CONSTRAINT pk_interconnector PRIMARY KEY (flow_id)
) USING DELTA
PARTITIONED BY (DATE(interval_datetime), interconnector_id);

CREATE INDEX IF NOT EXISTS idx_interconnector_datetime
ON apex.market_nem.interconnector_flows (interval_datetime);

COMMENT ON TABLE apex.market_nem.interconnector_flows IS
'Interconnector flows between regions from NEMWEB';

-- ============================================================================
-- Ingestion Logs (Track what's been loaded)
-- ============================================================================

CREATE TABLE IF NOT EXISTS apex.nemweb.ingestion_log (
  log_id STRING,
  data_type STRING,  -- 'DISPATCH_PRICES', 'PREDISPATCH', 'DEMAND', 'GENERATION'
  date_loaded DATE,  -- Date of data loaded
  region_id STRING,
  records_loaded BIGINT,
  records_failed BIGINT,
  start_timestamp TIMESTAMP,
  end_timestamp TIMESTAMP,
  duration_seconds DOUBLE,
  status STRING,  -- 'SUCCESS', 'PARTIAL', 'FAILED'
  error_message STRING,
  CONSTRAINT pk_ingestion_log PRIMARY KEY (log_id)
) USING DELTA
PARTITIONED BY (DATE(start_timestamp), data_type);

CREATE INDEX IF NOT EXISTS idx_ingestion_date
ON apex.nemweb.ingestion_log (date_loaded, data_type);

COMMENT ON TABLE apex.nemweb.ingestion_log IS
'Tracks NEMWEB data ingestion jobs - success/failure, record counts, timing';

-- ============================================================================
-- Data Quality Metrics
-- ============================================================================

CREATE TABLE IF NOT EXISTS apex.nemweb.data_quality_metrics (
  metric_id STRING,
  check_timestamp TIMESTAMP,
  data_type STRING,
  region_id STRING,
  date_checked DATE,
  metric_name STRING,  -- 'COMPLETENESS', 'TIMELINESS', 'ACCURACY', 'CONSISTENCY'
  metric_value DOUBLE,
  threshold_value DOUBLE,
  passed BOOLEAN,
  details STRING,
  CONSTRAINT pk_quality_metrics PRIMARY KEY (metric_id)
) USING DELTA
PARTITIONED BY (DATE(check_timestamp), data_type);

CREATE INDEX IF NOT EXISTS idx_quality_timestamp
ON apex.nemweb.data_quality_metrics (check_timestamp);

COMMENT ON TABLE apex.nemweb.data_quality_metrics IS
'Data quality checks for NEMWEB ingestion - completeness, accuracy, timeliness';

-- ============================================================================
-- Data Freshness View (Latest data available)
-- ============================================================================

CREATE OR REPLACE VIEW apex.nemweb.data_freshness AS
SELECT
  data_type,
  region_id,
  MAX(interval_datetime) AS latest_data_timestamp,
  TIMESTAMPDIFF(MINUTE, MAX(interval_datetime), CURRENT_TIMESTAMP()) AS minutes_since_latest,
  COUNT(*) AS total_records,
  MAX(ingestion_timestamp) AS last_ingestion_timestamp
FROM (
  SELECT 'DISPATCH_PRICES' AS data_type, region_id, interval_datetime, ingestion_timestamp
  FROM apex.market_nem.dispatch_prices
  WHERE DATE(interval_datetime) >= CURRENT_DATE() - INTERVAL 7 DAYS

  UNION ALL

  SELECT 'PREDISPATCH_FORECASTS' AS data_type, region_id, interval_datetime, ingestion_timestamp
  FROM apex.market_nem.predispatch_forecasts
  WHERE DATE(interval_datetime) >= CURRENT_DATE() - INTERVAL 7 DAYS

  UNION ALL

  SELECT 'DEMAND_ACTUAL' AS data_type, region_id, interval_datetime, ingestion_timestamp
  FROM apex.market_nem.demand_actual
  WHERE DATE(interval_datetime) >= CURRENT_DATE() - INTERVAL 7 DAYS
)
GROUP BY data_type, region_id
ORDER BY data_type, region_id;

-- ============================================================================
-- Ingestion Summary View (Daily statistics)
-- ============================================================================

CREATE OR REPLACE VIEW apex.nemweb.ingestion_summary AS
SELECT
  DATE(start_timestamp) AS ingestion_date,
  data_type,
  region_id,
  COUNT(*) AS total_jobs,
  SUM(CASE WHEN status = 'SUCCESS' THEN 1 ELSE 0 END) AS successful_jobs,
  SUM(CASE WHEN status = 'FAILED' THEN 1 ELSE 0 END) AS failed_jobs,
  SUM(records_loaded) AS total_records_loaded,
  SUM(records_failed) AS total_records_failed,
  AVG(duration_seconds) AS avg_duration_seconds,
  MAX(end_timestamp) AS last_run_timestamp
FROM apex.nemweb.ingestion_log
WHERE start_timestamp >= CURRENT_DATE() - INTERVAL 30 DAYS
GROUP BY DATE(start_timestamp), data_type, region_id
ORDER BY ingestion_date DESC, data_type, region_id;

-- ============================================================================
-- Price Statistics View (Daily aggregates for quick analysis)
-- ============================================================================

CREATE OR REPLACE VIEW apex.market_nem.daily_price_stats AS
SELECT
  DATE(interval_datetime) AS price_date,
  region_id,
  COUNT(*) AS interval_count,
  AVG(rrp) AS avg_price,
  MIN(rrp) AS min_price,
  MAX(rrp) AS max_price,
  STDDEV(rrp) AS price_volatility,
  PERCENTILE(rrp, 0.5) AS median_price,
  PERCENTILE(rrp, 0.95) AS p95_price,
  AVG(demand_mw) AS avg_demand_mw,
  MAX(demand_mw) AS peak_demand_mw,
  SUM(CASE WHEN rrp > 300 THEN 1 ELSE 0 END) AS high_price_intervals,  -- Count of >$300/MWh
  data_source
FROM apex.market_nem.dispatch_prices
WHERE interval_datetime >= CURRENT_DATE() - INTERVAL 90 DAYS
GROUP BY DATE(interval_datetime), region_id, data_source
ORDER BY price_date DESC, region_id;

-- ============================================================================
-- Forecast Accuracy View (Compare pre-dispatch vs actual)
-- ============================================================================

CREATE OR REPLACE VIEW apex.market_nem.forecast_accuracy AS
SELECT
  DATE(a.interval_datetime) AS forecast_date,
  a.region_id,
  COUNT(*) AS interval_count,
  AVG(f.forecast_price) AS avg_forecast_price,
  AVG(a.rrp) AS avg_actual_price,
  AVG(ABS(f.forecast_price - a.rrp)) AS mae,  -- Mean Absolute Error
  AVG(ABS(f.forecast_price - a.rrp) / NULLIF(a.rrp, 0) * 100) AS mape,  -- Mean Absolute Percentage Error
  SQRT(AVG(POW(f.forecast_price - a.rrp, 2))) AS rmse,  -- Root Mean Square Error
  CORR(f.forecast_price, a.rrp) AS correlation
FROM apex.market_nem.dispatch_prices a
INNER JOIN apex.market_nem.predispatch_forecasts f
  ON a.interval_datetime = f.interval_datetime
  AND a.region_id = f.region_id
  AND f.forecast_horizon_minutes <= 60  -- Only 1-hour ahead forecasts
WHERE a.interval_datetime >= CURRENT_DATE() - INTERVAL 30 DAYS
  AND a.data_source = 'NEMWEB'
GROUP BY DATE(a.interval_datetime), a.region_id
ORDER BY forecast_date DESC, a.region_id;
