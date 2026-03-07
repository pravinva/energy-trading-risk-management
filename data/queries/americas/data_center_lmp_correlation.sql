SELECT l.node_id, date_trunc('month', l.interval_datetime) as month_start, avg(l.lmp) as avg_lmp,
       avg(l.congestion_component) as avg_congestion, avg(l.lmp) - avg(h.lmp) as avg_basis_vs_hub
FROM serverless_sandbox_tladem_catalog.nexus_americas.lmp_realtime l
LEFT JOIN serverless_sandbox_tladem_catalog.nexus_americas.lmp_realtime h
  ON h.iso_id=l.iso_id AND h.node_id=concat(l.iso_id,'_NODE_001') AND date_trunc('month',h.interval_datetime)=date_trunc('month',l.interval_datetime)
WHERE l.iso_id = :iso_id
GROUP BY l.node_id, date_trunc('month', l.interval_datetime)
ORDER BY month_start;
