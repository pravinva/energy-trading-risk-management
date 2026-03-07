DELETE FROM serverless_sandbox_tladem_catalog.nexus_europe.cross_border_flows;
INSERT INTO serverless_sandbox_tladem_catalog.nexus_europe.cross_border_flows
SELECT row_number() OVER (ORDER BY interval_datetime, from_zone, to_zone),
       interval_datetime, from_zone, to_zone,
       cast(flow_mw as decimal(12,2)), cast(atc_mw as decimal(12,2)), cast(atc_mw as decimal(12,2)), 'SIMULATED'
FROM (
  SELECT t.interval_datetime, c.from_zone, c.to_zone, c.atc_mw,
         greatest(0, least(c.atc_mw*1.02, c.atc_mw*(0.55 + rand()*0.55))) as flow_mw
  FROM (SELECT explode(sequence(timestamp'2025-01-01 00:00:00', timestamp'2026-03-01 00:00:00', interval 1 hour)) as interval_datetime) t
  CROSS JOIN (
    SELECT 'DE' as from_zone, 'FR' as to_zone, 3500 as atc_mw UNION ALL
    SELECT 'DE','NL',3000 UNION ALL
    SELECT 'DE','BE',2500 UNION ALL
    SELECT 'FR','BE',1800 UNION ALL
    SELECT 'FR','ES',2200 UNION ALL
    SELECT 'NO1','DE',1500
  ) c
) r;
