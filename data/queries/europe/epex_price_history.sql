SELECT bidding_zone, delivery_datetime, price_eur_mwh, volume_mwh, market_time_unit_minutes
FROM serverless_sandbox_tladem_catalog.nexus_europe.epex_day_ahead_prices
WHERE (:bidding_zone IS NULL OR bidding_zone = :bidding_zone)
  AND delivery_datetime >= current_timestamp() - make_interval(0,0,0,0,:hours)
ORDER BY delivery_datetime;
