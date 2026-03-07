USE CATALOG apex_fresh;

INSERT INTO apex_fresh.analytics.model_performance
WITH markets AS (
  SELECT 'NEM' AS market, interval_datetime AS ts, CAST(rrp AS DOUBLE) AS actual
  FROM apex_fresh.market_nem.prices
  UNION ALL
  SELECT 'EPEX' AS market, delivery_datetime AS ts, CAST(price_eur_mwh AS DOUBLE) AS actual
  FROM apex_fresh.market_epex.prices
  UNION ALL
  SELECT 'ERCOT' AS market, interval_datetime AS ts, CAST(lmp AS DOUBLE) AS actual
  FROM apex_fresh.market_ercot.lmp
),
scored AS (
  SELECT market, ts, actual,
         AVG(actual) OVER (
           PARTITION BY market ORDER BY ts
           ROWS BETWEEN 24 PRECEDING AND 1 PRECEDING
         ) AS predicted
  FROM markets
),
scored_w_mean AS (
  SELECT market, ts, actual, predicted, AVG(actual) OVER (PARTITION BY market) AS market_mean
  FROM scored
),
metrics AS (
  SELECT
    market,
    AVG(ABS(actual - predicted) / NULLIF(actual, 0)) * 100 AS mape,
    SQRT(AVG(POWER(actual - predicted, 2))) AS rmse,
    1 - (SUM(POWER(actual - predicted, 2)) / NULLIF(SUM(POWER(actual - market_mean, 2)), 0)) AS r2
  FROM scored_w_mean
  WHERE predicted IS NOT NULL
  GROUP BY market
)
SELECT
  CONCAT('price-forecast-', lower(market), '@champion') AS model_name,
  market,
  COALESCE(mape, 0) AS mape,
  COALESCE(rmse, 0) AS rmse,
  COALESCE(r2, 0) AS r2,
  current_timestamp() AS run_timestamp
FROM metrics;

INSERT INTO apex_fresh.analytics.backtest_runs
WITH t AS (
  SELECT market,
         CASE WHEN upper(direction) = 'SELL'
           THEN CAST(price AS DOUBLE) * CAST(volume_mw AS DOUBLE)
           ELSE -CAST(price AS DOUBLE) * CAST(volume_mw AS DOUBLE)
         END AS pnl
  FROM apex_fresh.trading.trades
),
agg AS (
  SELECT
    market,
    COUNT(*) AS trades,
    AVG(CASE WHEN pnl > 0 THEN 1.0 ELSE 0.0 END) AS win_rate,
    SUM(pnl) AS total_pnl,
    CASE WHEN STDDEV_SAMP(pnl) = 0 THEN 0.0 ELSE AVG(pnl) / STDDEV_SAMP(pnl) END AS sharpe
  FROM t
  GROUP BY market
)
SELECT
  CONCAT(market, ' Directional Strategy') AS strategy,
  market,
  trades,
  COALESCE(win_rate, 0) AS win_rate,
  COALESCE(total_pnl, 0) AS total_pnl,
  COALESCE(sharpe, 0) AS sharpe,
  current_timestamp() AS run_timestamp
FROM agg;
