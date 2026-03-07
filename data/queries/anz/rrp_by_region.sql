SELECT interval_datetime, region_id, rrp, totaldemand, lower5min, raise5min, raisereg, lowerreg
FROM serverless_sandbox_tladem_catalog.nexus_anz.nem_dispatch_intervals
WHERE (:region_id IS NULL OR region_id = :region_id)
  AND interval_datetime >= current_timestamp() - make_interval(0,0,0,0,:hours)
ORDER BY interval_datetime DESC;
