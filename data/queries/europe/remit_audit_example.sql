SELECT delivery_datetime, bidding_zone, price_eur_mwh, data_source, current_timestamp() as recorded_at
FROM serverless_sandbox_tladem_catalog.nexus_europe.epex_day_ahead_prices
WHERE bidding_zone = :bidding_zone
  AND date(delivery_datetime) = date(:audit_date)
ORDER BY delivery_datetime;
