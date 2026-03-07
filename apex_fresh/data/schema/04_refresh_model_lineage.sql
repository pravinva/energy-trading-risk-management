USE CATALOG apex_fresh;

CREATE TABLE IF NOT EXISTS apex_fresh.analytics.model_lineage (
  market STRING,
  model_name STRING,
  run_timestamp TIMESTAMP,
  training_start_utc TIMESTAMP,
  training_end_utc TIMESTAMP,
  feature_set STRING,
  feature_hash STRING
);

DELETE FROM apex_fresh.analytics.model_lineage
WHERE run_timestamp < current_timestamp() - INTERVAL 7 DAYS;

INSERT INTO apex_fresh.analytics.model_lineage
WITH latest_models AS (
  SELECT
    market,
    max_by(model_name, run_timestamp) AS model_name,
    MAX(run_timestamp) AS run_timestamp
  FROM apex_fresh.analytics.model_performance
  GROUP BY market
),
training_window AS (
  SELECT 'NEM' AS market, MIN(interval_datetime) AS training_start_utc, MAX(interval_datetime) AS training_end_utc
  FROM apex_fresh.market_nem.prices
  UNION ALL
  SELECT 'EPEX' AS market, MIN(delivery_datetime) AS training_start_utc, MAX(delivery_datetime) AS training_end_utc
  FROM apex_fresh.market_epex.prices
  UNION ALL
  SELECT 'ERCOT' AS market, MIN(interval_datetime) AS training_start_utc, MAX(interval_datetime) AS training_end_utc
  FROM apex_fresh.market_ercot.lmp
),
features AS (
  SELECT
    'NEM' AS market,
    'lag_1,lag_2,lag_6,roll_mean_6,roll_std_6,hour,dow' AS feature_set
  UNION ALL
  SELECT
    'EPEX' AS market,
    'lag_1,lag_2,lag_6,roll_mean_6,roll_std_6,hour,dow' AS feature_set
  UNION ALL
  SELECT
    'ERCOT' AS market,
    'lag_1,lag_2,lag_6,roll_mean_6,roll_std_6,hour,dow' AS feature_set
)
SELECT
  m.market,
  m.model_name,
  m.run_timestamp,
  w.training_start_utc,
  w.training_end_utc,
  f.feature_set,
  sha2(f.feature_set, 256) AS feature_hash
FROM latest_models m
LEFT JOIN training_window w ON m.market = w.market
LEFT JOIN features f ON m.market = f.market;
