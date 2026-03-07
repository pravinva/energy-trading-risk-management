DELETE FROM serverless_sandbox_tladem_catalog.nexus_europe.spark_spreads;
INSERT INTO serverless_sandbox_tladem_catalog.nexus_europe.spark_spreads
SELECT row_number() OVER (ORDER BY calculation_datetime, bidding_zone),
       calculation_datetime, bidding_zone,
       cast(power_price as decimal(12,4)), cast(gas_price_mmbtu as decimal(12,4)), cast(0.45 as decimal(8,4)),
       cast(ets_price as decimal(10,4)),
       cast(power_price - gas_price_mmbtu*0.45 as decimal(12,4)),
       cast((power_price - gas_price_mmbtu*0.45) - ets_price*0.35 as decimal(12,4)),
       'SIMULATED'
FROM (
  SELECT e.delivery_datetime as calculation_datetime, e.bidding_zone,
         cast(e.price_eur_mwh as double) as power_price,
         30 + rand()*12 as gas_price_mmbtu,
         cast(c.eua_price_eur as double) as ets_price
  FROM serverless_sandbox_tladem_catalog.nexus_europe.epex_day_ahead_prices e
  LEFT JOIN serverless_sandbox_tladem_catalog.nexus_europe.ets_carbon_prices c
    ON date(e.delivery_datetime) = c.price_date
) s;
