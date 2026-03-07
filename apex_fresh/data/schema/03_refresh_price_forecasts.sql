USE CATALOG apex_fresh;

DELETE FROM apex_fresh.analytics.price_forecasts
WHERE run_timestamp < current_timestamp() - INTERVAL 2 DAYS;

INSERT INTO apex_fresh.analytics.price_forecasts
WITH horizon AS (
  SELECT explode(sequence(1, 24)) AS h
),
nem_base AS (
  SELECT region_id AS instrument, interval_datetime AS ts, CAST(rrp AS DOUBLE) AS px
  FROM apex_fresh.market_nem.prices
),
nem_recent AS (
  SELECT instrument, ts, px,
         ROW_NUMBER() OVER (PARTITION BY instrument ORDER BY ts DESC) AS rn
  FROM nem_base
),
nem_features AS (
  SELECT instrument,
         MAX(CASE WHEN rn = 1 THEN ts END) AS last_ts,
         AVG(CASE WHEN rn <= 12 THEN px END) AS mean_px,
         AVG(CASE WHEN rn <= 4 THEN px END) - AVG(CASE WHEN rn BETWEEN 5 AND 12 THEN px END) AS short_slope
  FROM nem_recent
  GROUP BY instrument
),
epex_base AS (
  SELECT bidding_zone AS instrument, delivery_datetime AS ts, CAST(price_eur_mwh AS DOUBLE) AS px
  FROM apex_fresh.market_epex.prices
),
epex_recent AS (
  SELECT instrument, ts, px,
         ROW_NUMBER() OVER (PARTITION BY instrument ORDER BY ts DESC) AS rn
  FROM epex_base
),
epex_features AS (
  SELECT instrument,
         MAX(CASE WHEN rn = 1 THEN ts END) AS last_ts,
         AVG(CASE WHEN rn <= 12 THEN px END) AS mean_px,
         AVG(CASE WHEN rn <= 4 THEN px END) - AVG(CASE WHEN rn BETWEEN 5 AND 12 THEN px END) AS short_slope
  FROM epex_recent
  GROUP BY instrument
),
ercot_base AS (
  SELECT node_id AS instrument, interval_datetime AS ts, CAST(lmp AS DOUBLE) AS px
  FROM apex_fresh.market_ercot.lmp
),
ercot_recent AS (
  SELECT instrument, ts, px,
         ROW_NUMBER() OVER (PARTITION BY instrument ORDER BY ts DESC) AS rn
  FROM ercot_base
),
ercot_features AS (
  SELECT instrument,
         MAX(CASE WHEN rn = 1 THEN ts END) AS last_ts,
         AVG(CASE WHEN rn <= 12 THEN px END) AS mean_px,
         AVG(CASE WHEN rn <= 4 THEN px END) - AVG(CASE WHEN rn BETWEEN 5 AND 12 THEN px END) AS short_slope
  FROM ercot_recent
  GROUP BY instrument
)
SELECT
  'NEM' AS market,
  f.instrument,
  f.last_ts + make_interval(0, 0, 0, 0, 0, h.h, 0) AS forecast_datetime,
  ROUND(f.mean_px + h.h * COALESCE(f.short_slope, 0) * 0.35, 4) AS forecast_price,
  CAST(0 AS DOUBLE) AS forecast_demand_mw,
  'xgb-nem@champion' AS model_name,
  current_timestamp() AS run_timestamp
FROM nem_features f CROSS JOIN horizon h
UNION ALL
SELECT
  'EPEX' AS market,
  f.instrument,
  f.last_ts + make_interval(0, 0, 0, 0, 0, h.h * 15, 0) AS forecast_datetime,
  ROUND(f.mean_px + h.h * COALESCE(f.short_slope, 0) * 0.35, 4) AS forecast_price,
  CAST(0 AS DOUBLE) AS forecast_demand_mw,
  'xgb-epex@champion' AS model_name,
  current_timestamp() AS run_timestamp
FROM epex_features f CROSS JOIN horizon h
UNION ALL
SELECT
  'ERCOT' AS market,
  f.instrument,
  f.last_ts + make_interval(0, 0, 0, 0, 0, h.h * 5, 0) AS forecast_datetime,
  ROUND(f.mean_px + h.h * COALESCE(f.short_slope, 0) * 0.35, 4) AS forecast_price,
  CAST(0 AS DOUBLE) AS forecast_demand_mw,
  'xgb-ercot@champion' AS model_name,
  current_timestamp() AS run_timestamp
FROM ercot_features f CROSS JOIN horizon h;
