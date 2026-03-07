DELETE FROM serverless_sandbox_tladem_catalog.nexus_americas.ercot_bess_telemetry;
INSERT INTO serverless_sandbox_tladem_catalog.nexus_americas.ercot_bess_telemetry
SELECT row_number() OVER (ORDER BY recorded_at, resource_id), resource_id, recorded_at,
       cast(least(100, greatest(0, soc)) as decimal(5,2)), cast(output_mw as decimal(10,2)),
       cast(drrs_mw as decimal(10,2)), cast(reg_up_mw as decimal(10,2)), cast(reg_down_mw as decimal(10,2)),
       cast(tb1 as decimal(10,4)), cast(tb4 as decimal(10,4)), cast(rtcb_signal as decimal(10,4)), 'SIMULATED'
FROM (
  SELECT t.recorded_at, a.resource_id,
         55 + CASE WHEN hour(t.recorded_at) BETWEEN 9 AND 16 THEN 25 WHEN hour(t.recorded_at) BETWEEN 18 AND 21 THEN -30 ELSE 0 END + rand()*8-4 as soc,
         CASE WHEN hour(t.recorded_at) BETWEEN 9 AND 16 THEN -(5+rand()*50)
              WHEN hour(t.recorded_at) BETWEEN 18 AND 21 THEN 10+rand()*70
              ELSE rand()*8-4 END as output_mw,
         CASE WHEN t.recorded_at >= timestamp'2025-12-05 00:00:00' THEN a.capacity_mw*(rand()*0.5) ELSE null END as drrs_mw,
         rand()*20 as reg_up_mw,
         rand()*20 as reg_down_mw,
         10 + rand()*60 as tb1,
         20 + rand()*100 as tb4,
         CASE WHEN t.recorded_at >= timestamp'2025-12-05 00:00:00' THEN rand()*150 ELSE null END as rtcb_signal
  FROM (SELECT explode(sequence(timestamp'2025-01-01 00:00:00', timestamp'2026-03-01 00:00:00', interval 5 minutes)) as recorded_at) t
  CROSS JOIN (SELECT resource_id, capacity_mw FROM serverless_sandbox_tladem_catalog.nexus_americas.ercot_bess_assets) a
) s;
