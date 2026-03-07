DELETE FROM serverless_sandbox_tladem_catalog.nexus_anz.nem_dispatch_intervals;
INSERT INTO serverless_sandbox_tladem_catalog.nexus_anz.nem_dispatch_intervals
SELECT row_number() OVER (ORDER BY interval_datetime, region_id) AS dispatch_interval_id, interval_datetime, region_id,
       cast(rrp as decimal(12,4)), cast(rrp + rand()*5 as decimal(12,4)),
       cast(totaldemand as decimal(12,2)), cast(availablegeneration as decimal(12,2)), cast(netinterchange as decimal(12,2)),
       cast(lower5min as decimal(12,4)), cast(lower60sec as decimal(12,4)), cast(lower6sec as decimal(12,4)),
       cast(raise5min as decimal(12,4)), cast(raise60sec as decimal(12,4)), cast(raise6sec as decimal(12,4)),
       cast(lowerreg as decimal(12,4)), cast(raisereg as decimal(12,4)), 'SIMULATED'
FROM (
  SELECT t.interval_datetime, r.region_id,
         greatest(-80, ((75 + rand()*50)
           + CASE WHEN hour(t.interval_datetime) BETWEEN 10 AND 14 THEN -30 ELSE 0 END
           + CASE WHEN hour(t.interval_datetime) BETWEEN 17 AND 20 THEN 40 ELSE 0 END
           + CASE WHEN hour(t.interval_datetime) >= 23 OR hour(t.interval_datetime) <= 5 THEN -15 ELSE 0 END
           + CASE WHEN r.region_id='SA' THEN 20 ELSE 0 END)
           * CASE WHEN dayofweek(t.interval_datetime) IN (1,7) THEN 0.8 ELSE 1 END
           * CASE WHEN rand() > 0.997 THEN (40 + rand()*120) ELSE 1 END) as rrp,
         5000 + 3000 * sin(2*pi()*(hour(t.interval_datetime)-8)/24.0) + rand()*500 as totaldemand,
         7000 + 2000 * sin(2*pi()*(hour(t.interval_datetime)-6)/24.0) + rand()*400 as availablegeneration,
         rand()*400 - 200 as netinterchange,
         2 + rand()*5 + CASE WHEN rand()>0.995 THEN 80 ELSE 0 END as raise5min,
         1 + rand()*4 as raise60sec,
         2 + rand()*5 + CASE WHEN rand()>0.995 THEN 100 ELSE 0 END as raise6sec,
         2 + rand()*5 + CASE WHEN rand()>0.995 THEN 70 ELSE 0 END as lower5min,
         1 + rand()*4 as lower60sec,
         2 + rand()*5 + CASE WHEN rand()>0.995 THEN 90 ELSE 0 END as lower6sec,
         1 + rand()*3 as raisereg,
         1 + rand()*3 as lowerreg
  FROM (SELECT explode(sequence(timestamp'2025-01-01 00:00:00', timestamp'2026-03-01 00:00:00', interval 5 minutes)) as interval_datetime) t
  CROSS JOIN (SELECT explode(array('QLD','NSW','VIC','SA')) as region_id) r
) x;
