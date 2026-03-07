WITH pjm AS (
  SELECT date(interval_datetime) as d, avg(lmp) as pjm_aep_hub_price
  FROM serverless_sandbox_tladem_catalog.nexus_americas.lmp_realtime
  WHERE iso_id='PJM' AND node_id='PJM_NODE_001'
  GROUP BY date(interval_datetime)
), ercot AS (
  SELECT date(interval_datetime) as d, avg(lmp) as ercot_houston_price
  FROM serverless_sandbox_tladem_catalog.nexus_americas.lmp_realtime
  WHERE iso_id='ERCOT' AND node_id='ERCOT_NODE_001'
  GROUP BY date(interval_datetime)
)
SELECT p.d as date, p.pjm_aep_hub_price, e.ercot_houston_price, p.pjm_aep_hub_price - e.ercot_houston_price as spread,
       CASE WHEN p.pjm_aep_hub_price - e.ercot_houston_price > 0.5 THEN 'PJM_PREMIUM'
            WHEN p.pjm_aep_hub_price - e.ercot_houston_price < -0.5 THEN 'ERCOT_PREMIUM'
            ELSE 'FLAT' END as spread_direction
FROM pjm p JOIN ercot e ON p.d=e.d
ORDER BY date;
