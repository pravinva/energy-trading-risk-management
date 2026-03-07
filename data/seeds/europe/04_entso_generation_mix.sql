DELETE FROM serverless_sandbox_tladem_catalog.nexus_europe.entso_generation_mix;
INSERT INTO serverless_sandbox_tladem_catalog.nexus_europe.entso_generation_mix
SELECT row_number() OVER (ORDER BY interval_datetime, bidding_zone, fuel_type),
       interval_datetime, bidding_zone, fuel_type,
       cast(generation_mw as decimal(12,2)), 'SIMULATED'
FROM (
  SELECT t.interval_datetime, z.bidding_zone, f.fuel_type,
    CASE
      WHEN f.fuel_type = 'Nuclear' AND z.bidding_zone = 'FR' THEN 40000 + rand()*5000
      WHEN f.fuel_type = 'Nuclear' THEN 7000 + rand()*1200
      WHEN f.fuel_type = 'Solar' THEN CASE WHEN hour(t.interval_datetime) BETWEEN 7 AND 18 THEN 4000 + rand()*30000 ELSE 0 END
      WHEN f.fuel_type = 'Wind Onshore' THEN rand()*30000
      WHEN f.fuel_type = 'Wind Offshore' THEN rand()*8000
      WHEN f.fuel_type = 'Gas' THEN 5000 + rand()*20000
      WHEN f.fuel_type = 'Coal' THEN greatest(0, 9000 - (datediff(date'2026-03-01', date(t.interval_datetime))/30.0)*120 + rand()*500)
      ELSE 1000 + rand()*3000
    END as generation_mw
  FROM (SELECT explode(sequence(timestamp'2025-01-01 00:00:00', timestamp'2026-03-01 00:00:00', interval 1 hour)) as interval_datetime) t
  CROSS JOIN (SELECT explode(array('DE-LU','FR')) as bidding_zone) z
  CROSS JOIN (SELECT explode(array('Solar','Wind Onshore','Wind Offshore','Nuclear','Hydro','Gas','Coal','Lignite')) as fuel_type) f
) s;
