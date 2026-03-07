SELECT fuel_type, avg(generation_mw) as generation_mw
FROM serverless_sandbox_tladem_catalog.nexus_europe.entso_generation_mix
WHERE bidding_zone = :bidding_zone
  AND interval_datetime >= current_timestamp() - interval 6 hours
GROUP BY fuel_type
ORDER BY generation_mw DESC;
