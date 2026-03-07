SELECT calculation_datetime, power_price, gas_price_mmbtu, ets_price, spark_spread, clean_spark_spread
FROM serverless_sandbox_tladem_catalog.nexus_europe.spark_spreads
WHERE bidding_zone = :bidding_zone
  AND calculation_datetime >= current_timestamp() - interval 30 days
ORDER BY calculation_datetime;
