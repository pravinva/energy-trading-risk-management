SELECT settlement_date, energy_revenue,
       coalesce(fcas_raise5min_revenue,0)+coalesce(fcas_lower5min_revenue,0)+coalesce(fcas_raise6sec_revenue,0)+coalesce(fcas_lower6sec_revenue,0) as fcas_total_revenue,
       total_revenue
FROM serverless_sandbox_tladem_catalog.nexus_anz.settlement_revenues
WHERE duid = :duid
ORDER BY settlement_date DESC
LIMIT :days;
