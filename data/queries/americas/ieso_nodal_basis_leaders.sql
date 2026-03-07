SELECT p.node_id, n.node_name, avg(p.basis_spread) as avg_basis_spread, max(p.basis_spread) as max_basis_spread,
       avg(CASE WHEN p.basis_spread > 0 THEN 1 ELSE 0 END) * 100 as pct_hours_positive_basis
FROM serverless_sandbox_tladem_catalog.nexus_americas.ieso_nodal_prices p
LEFT JOIN serverless_sandbox_tladem_catalog.nexus_americas.iso_nodes n ON p.node_id=n.node_id
WHERE p.interval_datetime >= timestamp'2025-05-01 00:00:00'
GROUP BY p.node_id, n.node_name
ORDER BY avg_basis_spread DESC
LIMIT 10;
