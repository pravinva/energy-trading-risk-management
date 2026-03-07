WITH latest AS (
  SELECT duid, state_of_charge_pct, output_mw, row_number() OVER (PARTITION BY duid ORDER BY recorded_at DESC) as rn
  FROM serverless_sandbox_tladem_catalog.nexus_anz.bess_telemetry
), rev AS (
  SELECT duid, sum(case when settlement_date = current_date() then total_revenue else 0 end) as today_revenue,
         sum(total_revenue) as annual_revenue_ytd
  FROM serverless_sandbox_tladem_catalog.nexus_anz.settlement_revenues
  WHERE year(settlement_date)=year(current_date())
  GROUP BY duid
)
SELECT a.duid, a.asset_name, a.operator, a.region_id, a.capacity_mw, a.duration_hours,
       l.state_of_charge_pct as current_soc_pct, l.output_mw as current_output_mw,
       coalesce(r.today_revenue,0) as today_revenue, coalesce(r.annual_revenue_ytd,0) as annual_revenue_ytd
FROM serverless_sandbox_tladem_catalog.nexus_anz.bess_assets a
LEFT JOIN latest l ON a.duid=l.duid and l.rn=1
LEFT JOIN rev r ON a.duid=r.duid;
