SELECT interval_datetime as start_datetime, interval_datetime + interval 5 minutes as end_datetime, region_id, rrp as peak_rrp, 5 as duration_minutes
FROM serverless_sandbox_tladem_catalog.nexus_anz.nem_dispatch_intervals
WHERE rrp > 1000
  AND interval_datetime >= current_timestamp() - interval 90 days
ORDER BY interval_datetime DESC;
