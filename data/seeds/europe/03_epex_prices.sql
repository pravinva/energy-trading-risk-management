DELETE FROM serverless_sandbox_tladem_catalog.nexus_europe.epex_day_ahead_prices;
INSERT INTO serverless_sandbox_tladem_catalog.nexus_europe.epex_day_ahead_prices
SELECT row_number() OVER (ORDER BY delivery_datetime, bidding_zone),
       delivery_datetime, bidding_zone,
       cast(price as decimal(12,4)), cast(1500 + rand()*9000 as decimal(14,4)), mtu, date(delivery_datetime), 'SIMULATED'
FROM (
  SELECT ts as delivery_datetime, z.bidding_zone,
         CASE WHEN ts >= timestamp'2025-09-01 00:00:00' THEN 15 ELSE 60 END as mtu,
         greatest(-100,
           75 + rand()*40
           + CASE WHEN hour(ts) BETWEEN 10 AND 14 AND z.bidding_zone IN ('DE-LU','ES','FR') THEN -25 ELSE 0 END
           + CASE WHEN month(ts) IN (12,1,2) THEN 20 ELSE 0 END
           + CASE WHEN hour(ts) BETWEEN 18 AND 20 THEN 35 ELSE 0 END
           - CASE WHEN dayofweek(ts) IN (1,7) THEN 12 ELSE 0 END
         ) as price
  FROM (
    SELECT explode(sequence(timestamp'2024-01-01 00:00:00', timestamp'2025-08-31 23:00:00', interval 1 hour)) as ts
    UNION ALL
    SELECT explode(sequence(timestamp'2025-09-01 00:00:00', timestamp'2026-03-01 00:00:00', interval 15 minutes)) as ts
  ) t
  CROSS JOIN (SELECT explode(array('DE-LU','FR','BE','NL','ES','NO1','NO2','CH')) as bidding_zone) z
) q;
