DELETE FROM serverless_sandbox_tladem_catalog.nexus_americas.iso_nodes;
INSERT INTO serverless_sandbox_tladem_catalog.nexus_americas.iso_nodes
SELECT concat(iso_id, '_NODE_', lpad(cast(seq as string), 3, '0')),
       concat(iso_id, ' Node ', cast(seq as string)), iso_id,
       CASE WHEN seq = 1 THEN 'HUB' ELSE 'ZONE' END,
       cast(20 + rand()*30 as decimal(9,6)), cast(-120 + rand()*25 as decimal(9,6)),
       CASE WHEN seq = 1 THEN true ELSE false END,
       CASE WHEN seq = 1 THEN concat(iso_id, ' Hub') ELSE null END
FROM (
  SELECT 'ERCOT' as iso_id, explode(sequence(1,15)) as seq UNION ALL
  SELECT 'PJM', explode(sequence(1,12)) UNION ALL
  SELECT 'CAISO', explode(sequence(1,8)) UNION ALL
  SELECT 'MISO', explode(sequence(1,5)) UNION ALL
  SELECT 'SPP', explode(sequence(1,5)) UNION ALL
  SELECT 'NYISO', explode(sequence(1,4)) UNION ALL
  SELECT 'ISONE', explode(sequence(1,3)) UNION ALL
  SELECT 'AESO', explode(sequence(1,3)) UNION ALL
  SELECT 'IESO', explode(sequence(1,50))
) x;
