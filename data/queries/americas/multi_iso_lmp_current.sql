WITH ranked AS (
  SELECT l.iso_id, l.node_id, n.node_name, n.zone, l.lmp, l.energy_component, l.congestion_component, l.loss_component, l.interval_datetime,
         row_number() OVER (PARTITION BY l.iso_id ORDER BY l.interval_datetime DESC) as rn
  FROM serverless_sandbox_tladem_catalog.nexus_americas.lmp_realtime l
  LEFT JOIN serverless_sandbox_tladem_catalog.nexus_americas.iso_nodes n ON l.node_id=n.node_id
  WHERE (:iso_id IS NULL OR l.iso_id = :iso_id)
)
SELECT iso_id, node_id, node_name, zone, lmp, energy_component, congestion_component, loss_component, interval_datetime
FROM ranked WHERE rn=1;
