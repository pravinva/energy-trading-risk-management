SELECT CASE WHEN recorded_at < timestamp'2025-12-05 00:00:00' THEN 'pre_rtcb' ELSE 'post_rtcb' END as period,
       avg(tb4_spread) as avg_tb4_spread, avg(drrs_mw) as avg_drrs_mw, avg(output_mw) as avg_output_mw, avg(state_of_charge_pct) as avg_soc_pct, count(*) as total_count
FROM serverless_sandbox_tladem_catalog.nexus_americas.ercot_bess_telemetry
WHERE resource_id = :resource_id
GROUP BY 1
ORDER BY period;
