DELETE FROM serverless_sandbox_tladem_catalog.nexus_americas.ieso_nodal_prices;
INSERT INTO serverless_sandbox_tladem_catalog.nexus_americas.ieso_nodal_prices
SELECT row_number() OVER (ORDER BY interval_datetime, node_id), node_id, interval_datetime,
       cast(lmp_cad as decimal(12,4)), cast(ontario_zonal_price as decimal(12,4)), cast(lmp_cad-ontario_zonal_price as decimal(12,4)), 'RTM', 'SIMULATED'
FROM (
  SELECT t.interval_datetime, n.node_id,
         75 + rand()*50 + CASE WHEN month(t.interval_datetime) IN (12,1,2) THEN 15 ELSE 0 END as ontario_zonal_price,
         75 + rand()*50 + CASE WHEN n.node_id like '%_001' OR n.node_id like '%_002' OR n.node_id like '%_003' THEN 20 ELSE (rand()*50-25) END as lmp_cad
  FROM (SELECT explode(sequence(timestamp'2025-05-01 00:00:00', timestamp'2026-03-01 00:00:00', interval 5 minutes)) as interval_datetime) t
  CROSS JOIN (SELECT node_id FROM serverless_sandbox_tladem_catalog.nexus_americas.iso_nodes WHERE iso_id='IESO') n
) x;
