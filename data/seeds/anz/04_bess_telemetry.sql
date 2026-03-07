DELETE FROM serverless_sandbox_tladem_catalog.nexus_anz.bess_telemetry;
INSERT INTO serverless_sandbox_tladem_catalog.nexus_anz.bess_telemetry
SELECT row_number() OVER (ORDER BY recorded_at, duid), duid, recorded_at,
       cast(least(100, greatest(0, soc_pct)) as decimal(5,2)), cast(output_mw as decimal(10,2)),
       cast(fcas_raise_mw as decimal(10,2)), cast(fcas_lower_mw as decimal(10,2)), cast(available_mw as decimal(10,2)),
       cast(temperature_c as decimal(6,2)), cast(cycle_count_today as decimal(6,1)), 'SIMULATED'
FROM (
  SELECT t.recorded_at, a.duid,
         50 + CASE WHEN hour(t.recorded_at) BETWEEN 9 AND 16 THEN 35 WHEN hour(t.recorded_at) BETWEEN 17 AND 22 THEN -30 ELSE 0 END + rand()*10 - 5 as soc_pct,
         CASE WHEN hour(t.recorded_at) BETWEEN 9 AND 16 THEN -(5 + rand()*40)
              WHEN hour(t.recorded_at) BETWEEN 17 AND 22 THEN (8 + rand()*60)
              ELSE rand()*6 - 3 END as output_mw,
         3 + rand()*20 as fcas_raise_mw,
         3 + rand()*20 as fcas_lower_mw,
         a.capacity_mw * (0.6 + rand()*0.4) as available_mw,
         18 + 10*sin(2*pi()*hour(t.recorded_at)/24.0) + CASE WHEN month(t.recorded_at) IN (12,1,2) THEN 8 ELSE 0 END + rand()*3 as temperature_c,
         1.0 + rand()*2.0 as cycle_count_today
  FROM (SELECT explode(sequence(timestamp'2025-01-01 00:00:00', timestamp'2026-03-01 00:00:00', interval 5 minutes)) as recorded_at) t
  CROSS JOIN (SELECT duid, capacity_mw FROM serverless_sandbox_tladem_catalog.nexus_anz.bess_assets) a
) z;
