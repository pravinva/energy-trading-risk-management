WITH latest_nem AS (
  SELECT region_id, CAST(rrp AS DOUBLE) AS px,
         ROW_NUMBER() OVER (PARTITION BY region_id ORDER BY interval_datetime DESC) AS rn
  FROM apex.market_nem.prices
),
latest_epex AS (
  SELECT bidding_zone, CAST(price_eur_mwh AS DOUBLE) AS px,
         ROW_NUMBER() OVER (PARTITION BY bidding_zone ORDER BY delivery_datetime DESC) AS rn
  FROM apex.market_epex.prices
),
latest_ercot AS (
  SELECT node_id, CAST(lmp AS DOUBLE) AS px,
         ROW_NUMBER() OVER (PARTITION BY node_id ORDER BY interval_datetime DESC) AS rn
  FROM apex.market_ercot.lmp
)
SELECT
  t.trade_id,
  t.trader_id,
  t.instrument_id,
  t.direction,
  t.volume_mw,
  t.price,
  t.source_system,
  t.ingested_at,
  CASE
    WHEN upper(t.direction) = 'BUY' THEN (COALESCE(mp.mark_price, t.price) - t.price) * t.volume_mw
    ELSE (t.price - COALESCE(mp.mark_price, t.price)) * t.volume_mw
  END AS mtm_pnl
FROM apex.trading.trades t
LEFT JOIN (
  SELECT 'NEM' AS market, region_id AS key_id, px AS mark_price FROM latest_nem WHERE rn = 1
  UNION ALL
  SELECT 'EPEX' AS market, bidding_zone AS key_id, px AS mark_price FROM latest_epex WHERE rn = 1
  UNION ALL
  SELECT 'ERCOT' AS market, node_id AS key_id, px AS mark_price FROM latest_ercot WHERE rn = 1
) mp
  ON upper(t.market) = mp.market
 AND (
      (upper(t.market) = 'NEM' AND split(t.instrument_id, '_')[0] = mp.key_id)
   OR (upper(t.market) = 'EPEX' AND split(t.instrument_id, '_')[0] = mp.key_id)
   OR (upper(t.market) = 'ERCOT' AND regexp_replace(t.instrument_id, '^ERCOT_', '') = mp.key_id)
 )
-- __MARKET_FILTER__
ORDER BY t.ingested_at DESC
LIMIT 1000;
