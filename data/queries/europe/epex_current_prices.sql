WITH ranked AS (
  SELECT bidding_zone, delivery_datetime, price_eur_mwh, volume_mwh, market_time_unit_minutes,
         row_number() OVER (PARTITION BY bidding_zone ORDER BY delivery_datetime DESC) as rn
  FROM serverless_sandbox_tladem_catalog.nexus_europe.epex_day_ahead_prices
)
SELECT bidding_zone, delivery_datetime, price_eur_mwh, volume_mwh, market_time_unit_minutes
FROM ranked WHERE rn=1;
