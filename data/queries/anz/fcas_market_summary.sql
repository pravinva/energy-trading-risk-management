SELECT region_id, avg(lower6sec) as lower6sec_avg, avg(raise6sec) as raise6sec_avg, avg(lowerreg) as lowerreg_avg, avg(raisereg) as raisereg_avg
FROM serverless_sandbox_tladem_catalog.nexus_anz.nem_dispatch_intervals
WHERE interval_datetime >= current_timestamp() - interval 30 minutes
GROUP BY region_id;
