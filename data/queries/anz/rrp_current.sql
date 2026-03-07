WITH ranked AS (
  SELECT region_id, rrp,
         lag(rrp) OVER (PARTITION BY region_id ORDER BY interval_datetime) as prev_rrp,
         row_number() OVER (PARTITION BY region_id ORDER BY interval_datetime DESC) as rn
  FROM serverless_sandbox_tladem_catalog.nexus_anz.nem_dispatch_intervals
)
SELECT region_id, rrp, coalesce(rrp-prev_rrp,0) as change_vs_prev,
       coalesce((rrp-prev_rrp)/nullif(prev_rrp,0)*100,0) as pct_change,
       rrp > 1000 as is_spike
FROM ranked WHERE rn = 1;
