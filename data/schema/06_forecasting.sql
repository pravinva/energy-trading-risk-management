-- Phase 1: Forecasting & Predictive Analytics Schema
-- Weather data, production forecasts, price predictions, and BUY/SELL volume forecasts

USE CATALOG apex;

-- Forecasting schema
CREATE SCHEMA IF NOT EXISTS forecasting;

-- Weather forecast data (temperature, wind, solar irradiance)
CREATE TABLE IF NOT EXISTS apex.forecasting.weather_forecast (
  forecast_id STRING,
  region_id STRING,
  forecast_datetime TIMESTAMP,
  temperature_celsius DOUBLE,
  wind_speed_ms DOUBLE,
  solar_irradiance_wm2 DOUBLE,
  precipitation_mm DOUBLE,
  humidity_percent DOUBLE,
  confidence_level STRING, -- 'HIGH', 'MEDIUM', 'LOW'
  forecast_horizon_hours INT,
  created_at TIMESTAMP
);

-- Production forecast by asset type (renewables, coal, gas, etc.)
CREATE TABLE IF NOT EXISTS apex.forecasting.production_forecast (
  forecast_id STRING,
  region_id STRING,
  forecast_datetime TIMESTAMP,
  asset_type STRING, -- 'RENEWABLES', 'NUCLEAR', 'COAL', 'GAS', 'BIOMASS'
  generation_mw DOUBLE,
  capacity_mw DOUBLE,
  efficiency_percent DOUBLE,
  availability_percent DOUBLE,
  confidence_level STRING,
  forecast_horizon_hours INT,
  created_at TIMESTAMP
);

-- Price forecast (day-ahead, intraday, imbalance)
CREATE TABLE IF NOT EXISTS apex.forecasting.price_forecast (
  forecast_id STRING,
  region_id STRING,
  instrument STRING,
  forecast_datetime TIMESTAMP,
  forecast_price DOUBLE,
  actual_price DOUBLE, -- NULL until actual data available
  error DOUBLE, -- Calculated after actual available
  abs_error DOUBLE,
  mape DOUBLE, -- Mean Absolute Percentage Error
  market_type STRING, -- 'DAY_AHEAD', 'INTRADAY', 'IMBALANCE'
  confidence_level STRING,
  forecast_horizon_hours INT,
  created_at TIMESTAMP
);

-- BUY/SELL daily volume forecast (15-day forecast)
CREATE TABLE IF NOT EXISTS apex.forecasting.volume_forecast (
  forecast_id STRING,
  region_id STRING,
  forecast_date DATE,
  forecast_type STRING, -- 'BUY' or 'SELL'
  volume_mwh DOUBLE,
  base_volume_mwh DOUBLE,
  weather_impact_pct DOUBLE,
  maintenance_impact_pct DOUBLE,
  outage_impact_pct DOUBLE,
  market_demand_factor DOUBLE,
  confidence_level STRING,
  created_at TIMESTAMP
);

-- Weather impact correlation (for analytics)
CREATE TABLE IF NOT EXISTS apex.forecasting.weather_impact (
  region_id STRING,
  weather_parameter STRING, -- 'TEMPERATURE', 'WIND', 'SOLAR', 'PRECIPITATION'
  price_correlation DOUBLE,
  price_impact_per_unit DOUBLE, -- e.g., +12.5% per 1°C
  volatility_impact DOUBLE,
  sample_size INT,
  last_updated TIMESTAMP
);

-- Generation mix historical (for trending)
CREATE TABLE IF NOT EXISTS apex.forecasting.generation_mix_historical (
  region_id STRING,
  reading_datetime TIMESTAMP,
  asset_type STRING,
  generation_mw DOUBLE,
  total_generation_mw DOUBLE,
  mix_percentage DOUBLE
);

-- Plant status and maintenance schedule
CREATE TABLE IF NOT EXISTS apex.forecasting.plant_status (
  event_id STRING,
  plant_name STRING,
  plant_type STRING, -- 'COAL', 'GAS', 'WIND', 'SOLAR', 'NUCLEAR'
  region_id STRING,
  event_type STRING, -- 'OUTAGE', 'MAINTENANCE', 'RAMP_UP', 'RAMP_DOWN'
  start_datetime TIMESTAMP,
  end_datetime TIMESTAMP,
  capacity_impact_mw DOUBLE,
  grid_impact STRING, -- 'HIGH', 'MEDIUM', 'LOW'
  description STRING,
  status STRING -- 'SCHEDULED', 'ACTIVE', 'COMPLETED'
);

-- Extreme weather events (for alerts)
CREATE TABLE IF NOT EXISTS apex.forecasting.extreme_events (
  event_id STRING,
  region_id STRING,
  event_type STRING, -- 'WIND_STORM', 'SOLAR_DROP', 'THUNDERSTORM', 'COLD_SNAP', 'HEATWAVE'
  severity STRING, -- 'HIGH', 'MEDIUM', 'LOW'
  start_datetime TIMESTAMP,
  end_datetime TIMESTAMP,
  impact_description STRING,
  price_impact_pct DOUBLE,
  trading_alert_level STRING, -- 'HIGH', 'MEDIUM', 'LOW'
  confidence_level DOUBLE,
  created_at TIMESTAMP
);

-- Model performance tracking (for MLflow integration)
CREATE TABLE IF NOT EXISTS apex.forecasting.model_performance (
  model_id STRING,
  model_name STRING,
  model_type STRING, -- 'WEATHER', 'PRICE', 'PRODUCTION', 'VOLUME'
  region_id STRING,
  mape DOUBLE,
  mae DOUBLE,
  rmse DOUBLE,
  r2_score DOUBLE,
  bias DOUBLE,
  evaluation_date DATE,
  training_data_period STRING,
  feature_count INT,
  algorithm STRING, -- 'LIGHTGBM', 'XGBOOST', 'ARIMA', etc.
  mlflow_run_id STRING,
  created_at TIMESTAMP
);

COMMENT ON TABLE apex.forecasting.weather_forecast IS 'Weather forecast data for energy trading analysis';
COMMENT ON TABLE apex.forecasting.production_forecast IS 'Energy production forecast by asset type';
COMMENT ON TABLE apex.forecasting.price_forecast IS 'Energy price forecasts with actuals for validation';
COMMENT ON TABLE apex.forecasting.volume_forecast IS '15-day BUY/SELL volume forecast with impact factors';
COMMENT ON TABLE apex.forecasting.plant_status IS 'Plant outages, maintenance, and ramp schedules';
COMMENT ON TABLE apex.forecasting.extreme_events IS 'Extreme weather events impacting trading';
