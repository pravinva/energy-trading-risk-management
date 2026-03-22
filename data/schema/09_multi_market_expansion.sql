-- ============================================================================
-- PHASE 5: MULTI-MARKET EXPANSION (EPEX & ERCOT)
-- Multi-currency support with EUR and USD
-- ============================================================================

-- ============================================================================
-- CURRENCY MANAGEMENT
-- ============================================================================

CREATE TABLE IF NOT EXISTS apex.core.currencies (
  currency_code STRING,  -- 'AUD', 'EUR', 'USD'
  currency_name STRING,
  currency_symbol STRING,  -- '$', '€', '$'
  decimal_places INT,
  is_base_currency BOOLEAN,  -- AUD is base
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
  CONSTRAINT pk_currencies PRIMARY KEY (currency_code)
) USING DELTA;

-- Insert supported currencies
INSERT INTO apex.core.currencies VALUES
  ('AUD', 'Australian Dollar', '$', 2, TRUE, CURRENT_TIMESTAMP()),
  ('EUR', 'Euro', '€', 2, FALSE, CURRENT_TIMESTAMP()),
  ('USD', 'US Dollar', '$', 2, FALSE, CURRENT_TIMESTAMP());

CREATE TABLE IF NOT EXISTS apex.core.exchange_rates (
  rate_id STRING,
  from_currency STRING,
  to_currency STRING,
  rate DOUBLE,
  rate_date DATE,
  rate_timestamp TIMESTAMP,
  source STRING,  -- 'ECB', 'RBA', 'MANUAL'
  is_active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
  CONSTRAINT pk_exchange_rates PRIMARY KEY (rate_id)
) USING DELTA
PARTITIONED BY (rate_date);

-- Create view for latest exchange rates
CREATE OR REPLACE VIEW apex.core.latest_exchange_rates AS
SELECT
  from_currency,
  to_currency,
  rate,
  rate_date,
  rate_timestamp,
  source
FROM (
  SELECT *,
    ROW_NUMBER() OVER (PARTITION BY from_currency, to_currency ORDER BY rate_timestamp DESC) AS rn
  FROM apex.core.exchange_rates
  WHERE is_active = TRUE
)
WHERE rn = 1;


-- ============================================================================
-- EPEX (EUROPEAN POWER EXCHANGE) - EUR
-- ============================================================================

-- EPEX Day-Ahead Auction Prices (Germany, France, Austria, etc.)
CREATE TABLE IF NOT EXISTS apex.market_epex.day_ahead_prices (
  price_id STRING,
  market_area STRING,  -- 'DE', 'FR', 'AT', 'NL', 'BE', etc.
  delivery_date DATE,
  delivery_hour INT,  -- 1-24
  delivery_start TIMESTAMP,
  delivery_end TIMESTAMP,
  price_eur_mwh DOUBLE,
  volume_mwh DOUBLE,
  data_source STRING DEFAULT 'EPEX',
  ingestion_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
  CONSTRAINT pk_epex_da_prices PRIMARY KEY (price_id)
) USING DELTA
PARTITIONED BY (delivery_date, market_area);

-- EPEX Intraday Continuous Prices
CREATE TABLE IF NOT EXISTS apex.market_epex.intraday_prices (
  trade_id STRING,
  market_area STRING,
  execution_time TIMESTAMP,
  delivery_start TIMESTAMP,
  delivery_end TIMESTAMP,
  price_eur_mwh DOUBLE,
  volume_mwh DOUBLE,
  product_type STRING,  -- 'Q15', 'Q30', 'H1', etc. (15min, 30min, hourly)
  data_source STRING DEFAULT 'EPEX',
  ingestion_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
  CONSTRAINT pk_epex_id_prices PRIMARY KEY (trade_id)
) USING DELTA
PARTITIONED BY (DATE(execution_time), market_area);

-- EPEX Generation Forecasts (Renewables)
CREATE TABLE IF NOT EXISTS apex.market_epex.generation_forecasts (
  forecast_id STRING,
  market_area STRING,
  forecast_timestamp TIMESTAMP,
  delivery_start TIMESTAMP,
  delivery_end TIMESTAMP,
  fuel_type STRING,  -- 'SOLAR', 'WIND_ONSHORE', 'WIND_OFFSHORE', 'NUCLEAR', etc.
  forecasted_mw DOUBLE,
  forecast_source STRING,
  ingestion_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
  CONSTRAINT pk_epex_gen_forecast PRIMARY KEY (forecast_id)
) USING DELTA
PARTITIONED BY (DATE(forecast_timestamp), market_area);

-- EPEX Demand Forecasts
CREATE TABLE IF NOT EXISTS apex.market_epex.demand_forecasts (
  forecast_id STRING,
  market_area STRING,
  forecast_timestamp TIMESTAMP,
  delivery_start TIMESTAMP,
  delivery_end TIMESTAMP,
  forecasted_demand_mw DOUBLE,
  forecast_source STRING,
  ingestion_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
  CONSTRAINT pk_epex_demand_forecast PRIMARY KEY (forecast_id)
) USING DELTA
PARTITIONED BY (DATE(forecast_timestamp), market_area);

-- EPEX Cross-Border Flows
CREATE TABLE IF NOT EXISTS apex.market_epex.cross_border_flows (
  flow_id STRING,
  from_area STRING,
  to_area STRING,
  timestamp TIMESTAMP,
  scheduled_flow_mw DOUBLE,
  actual_flow_mw DOUBLE,
  capacity_mw DOUBLE,
  data_source STRING DEFAULT 'ENTSOE',
  ingestion_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
  CONSTRAINT pk_epex_flows PRIMARY KEY (flow_id)
) USING DELTA
PARTITIONED BY (DATE(timestamp));


-- ============================================================================
-- ERCOT (ELECTRIC RELIABILITY COUNCIL OF TEXAS) - USD
-- ============================================================================

-- ERCOT Real-Time Settlement Point Prices (SPPs)
CREATE TABLE IF NOT EXISTS apex.market_ercot.real_time_prices (
  spp_id STRING,
  settlement_point STRING,  -- 'HB_NORTH', 'HB_SOUTH', 'HB_WEST', 'HB_HOUSTON', etc.
  interval_datetime TIMESTAMP,  -- 5-minute intervals
  spp_usd_mwh DOUBLE,  -- Settlement Point Price
  congestion_price_usd_mwh DOUBLE,
  loss_price_usd_mwh DOUBLE,
  data_source STRING DEFAULT 'ERCOT',
  ingestion_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
  CONSTRAINT pk_ercot_rt_prices PRIMARY KEY (spp_id)
) USING DELTA
PARTITIONED BY (DATE(interval_datetime), settlement_point);

-- ERCOT Day-Ahead Market Prices
CREATE TABLE IF NOT EXISTS apex.market_ercot.day_ahead_prices (
  dam_id STRING,
  settlement_point STRING,
  delivery_date DATE,
  delivery_hour INT,  -- 1-24
  delivery_interval INT,  -- 1-4 (15-minute intervals within hour)
  delivery_start TIMESTAMP,
  lmp_usd_mwh DOUBLE,  -- Locational Marginal Price
  energy_price_usd_mwh DOUBLE,
  congestion_price_usd_mwh DOUBLE,
  loss_price_usd_mwh DOUBLE,
  data_source STRING DEFAULT 'ERCOT',
  ingestion_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
  CONSTRAINT pk_ercot_dam_prices PRIMARY KEY (dam_id)
) USING DELTA
PARTITIONED BY (delivery_date, settlement_point);

-- ERCOT Load Forecasts
CREATE TABLE IF NOT EXISTS apex.market_ercot.load_forecasts (
  forecast_id STRING,
  forecast_type STRING,  -- 'SHORT_TERM', 'MID_TERM', 'LONG_TERM'
  forecast_timestamp TIMESTAMP,
  delivery_start TIMESTAMP,
  delivery_end TIMESTAMP,
  forecasted_load_mw DOUBLE,
  forecast_source STRING,
  ingestion_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
  CONSTRAINT pk_ercot_load_forecast PRIMARY KEY (forecast_id)
) USING DELTA
PARTITIONED BY (DATE(forecast_timestamp));

-- ERCOT Wind/Solar Generation (Actual)
CREATE TABLE IF NOT EXISTS apex.market_ercot.renewable_generation (
  generation_id STRING,
  timestamp TIMESTAMP,
  fuel_type STRING,  -- 'WIND', 'SOLAR'
  actual_generation_mw DOUBLE,
  installed_capacity_mw DOUBLE,
  capacity_factor DOUBLE,
  data_source STRING DEFAULT 'ERCOT',
  ingestion_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
  CONSTRAINT pk_ercot_renewable_gen PRIMARY KEY (generation_id)
) USING DELTA
PARTITIONED BY (DATE(timestamp), fuel_type);

-- ERCOT Ancillary Services Prices
CREATE TABLE IF NOT EXISTS apex.market_ercot.ancillary_services (
  as_id STRING,
  service_type STRING,  -- 'REG_UP', 'REG_DOWN', 'RRS', 'NONSPIN', 'ECRS'
  interval_datetime TIMESTAMP,
  price_usd_mw DOUBLE,
  cleared_capacity_mw DOUBLE,
  data_source STRING DEFAULT 'ERCOT',
  ingestion_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
  CONSTRAINT pk_ercot_as PRIMARY KEY (as_id)
) USING DELTA
PARTITIONED BY (DATE(interval_datetime), service_type);


-- ============================================================================
-- CURRENCY CONVERSION HELPER FUNCTIONS (FOR DISPLAY ONLY)
-- ============================================================================

-- Helper view for NEM prices with optional currency display
CREATE OR REPLACE VIEW apex.market_nem.prices_with_currency AS
SELECT
  p.*,
  'AUD' AS native_currency,
  p.rrp AS price_native,
  p.rrp * COALESCE(er_eur.rate, 0) AS price_eur_display,
  p.rrp * COALESCE(er_usd.rate, 0) AS price_usd_display
FROM apex.market_nem.dispatch_prices p
LEFT JOIN (SELECT rate FROM apex.core.latest_exchange_rates WHERE from_currency = 'AUD' AND to_currency = 'EUR' LIMIT 1) er_eur ON TRUE
LEFT JOIN (SELECT rate FROM apex.core.latest_exchange_rates WHERE from_currency = 'AUD' AND to_currency = 'USD' LIMIT 1) er_usd ON TRUE;

-- Helper view for EPEX prices with optional currency display
CREATE OR REPLACE VIEW apex.market_epex.prices_with_currency AS
SELECT
  p.*,
  'EUR' AS native_currency,
  p.price_eur_mwh AS price_native,
  p.price_eur_mwh / COALESCE(er_aud.rate, 1) AS price_aud_display,
  p.price_eur_mwh * COALESCE(er_usd.rate, 1) AS price_usd_display
FROM apex.market_epex.day_ahead_prices p
LEFT JOIN (SELECT rate FROM apex.core.latest_exchange_rates WHERE from_currency = 'EUR' AND to_currency = 'AUD' LIMIT 1) er_aud ON TRUE
LEFT JOIN (SELECT rate FROM apex.core.latest_exchange_rates WHERE from_currency = 'EUR' AND to_currency = 'USD' LIMIT 1) er_usd ON TRUE;

-- Helper view for ERCOT prices with optional currency display
CREATE OR REPLACE VIEW apex.market_ercot.prices_with_currency AS
SELECT
  p.*,
  'USD' AS native_currency,
  p.spp_usd_mwh AS price_native,
  p.spp_usd_mwh / COALESCE(er_aud.rate, 1) AS price_aud_display,
  p.spp_usd_mwh / COALESCE(er_eur.rate, 1) AS price_eur_display
FROM apex.market_ercot.real_time_prices p
LEFT JOIN (SELECT rate FROM apex.core.latest_exchange_rates WHERE from_currency = 'USD' AND to_currency = 'AUD' LIMIT 1) er_aud ON TRUE
LEFT JOIN (SELECT rate FROM apex.core.latest_exchange_rates WHERE from_currency = 'USD' AND to_currency = 'EUR' LIMIT 1) er_eur ON TRUE;


-- ============================================================================
-- MARKET METADATA
-- ============================================================================

CREATE TABLE IF NOT EXISTS apex.core.market_metadata (
  market_code STRING,  -- 'NEM', 'EPEX', 'ERCOT'
  market_name STRING,
  region STRING,  -- 'AUSTRALIA', 'EUROPE', 'TEXAS'
  currency_code STRING,
  timezone STRING,
  settlement_period_minutes INT,
  trading_start_time TIME,
  trading_end_time TIME,
  operator STRING,  -- 'AEMO', 'EPEX SPOT', 'ERCOT'
  api_endpoint STRING,
  is_active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
  CONSTRAINT pk_market_metadata PRIMARY KEY (market_code)
) USING DELTA;

INSERT INTO apex.core.market_metadata VALUES
  ('NEM', 'National Electricity Market', 'AUSTRALIA', 'AUD', 'Australia/Sydney', 5, '00:00:00', '23:59:59', 'AEMO', 'https://nemweb.com.au', TRUE, CURRENT_TIMESTAMP()),
  ('EPEX', 'European Power Exchange', 'EUROPE', 'EUR', 'Europe/Berlin', 60, '00:00:00', '23:59:59', 'EPEX SPOT', 'https://transparency.entsoe.eu', TRUE, CURRENT_TIMESTAMP()),
  ('ERCOT', 'Electric Reliability Council of Texas', 'TEXAS', 'USD', 'America/Chicago', 5, '00:00:00', '23:59:59', 'ERCOT', 'https://api.ercot.com', TRUE, CURRENT_TIMESTAMP());


-- ============================================================================
-- DATA QUALITY & INGESTION LOGS (Multi-Market)
-- ============================================================================

CREATE TABLE IF NOT EXISTS apex.core.market_ingestion_log (
  log_id STRING,
  market_code STRING,
  data_type STRING,
  date_loaded DATE,
  location STRING,  -- region_id, market_area, settlement_point
  records_loaded BIGINT,
  records_failed BIGINT,
  start_timestamp TIMESTAMP,
  end_timestamp TIMESTAMP,
  duration_seconds DOUBLE,
  status STRING,  -- 'SUCCESS', 'PARTIAL', 'FAILED'
  error_message STRING,
  CONSTRAINT pk_market_ingestion_log PRIMARY KEY (log_id)
) USING DELTA
PARTITIONED BY (market_code, date_loaded);


-- ============================================================================
-- INDICES FOR PERFORMANCE
-- ============================================================================

-- EPEX indices
CREATE INDEX IF NOT EXISTS idx_epex_da_delivery ON apex.market_epex.day_ahead_prices (delivery_date, market_area);
CREATE INDEX IF NOT EXISTS idx_epex_id_execution ON apex.market_epex.intraday_prices (execution_time, market_area);

-- ERCOT indices
CREATE INDEX IF NOT EXISTS idx_ercot_rt_interval ON apex.market_ercot.real_time_prices (interval_datetime, settlement_point);
CREATE INDEX IF NOT EXISTS idx_ercot_dam_delivery ON apex.market_ercot.day_ahead_prices (delivery_date, settlement_point);

-- Exchange rate index
CREATE INDEX IF NOT EXISTS idx_exchange_rate_date ON apex.core.exchange_rates (rate_date, from_currency, to_currency);

COMMENT ON TABLE apex.core.currencies IS 'Supported currencies for multi-market trading (AUD, EUR, USD)';
COMMENT ON TABLE apex.core.exchange_rates IS 'Historical and current exchange rates for currency conversion';
COMMENT ON TABLE apex.market_epex.day_ahead_prices IS 'EPEX day-ahead auction prices in EUR/MWh';
COMMENT ON TABLE apex.market_ercot.real_time_prices IS 'ERCOT real-time settlement point prices in USD/MWh';
COMMENT ON VIEW apex.analytics.unified_market_prices IS 'Unified view of prices across NEM, EPEX, and ERCOT with multi-currency conversion';
