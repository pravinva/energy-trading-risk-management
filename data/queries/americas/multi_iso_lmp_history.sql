WITH latest AS (
  SELECT max(interval_datetime) AS max_interval_datetime
  FROM serverless_sandbox_tladem_catalog.nexus_americas.lmp_realtime
  WHERE iso_id = :iso_id
)
SELECT
  t.iso_id,
  t.interval_datetime,
  avg(t.lmp) AS lmp,
  avg(t.energy_component) AS energy_component,
  avg(t.congestion_component) AS congestion_component,
  avg(t.loss_component) AS loss_component
FROM serverless_sandbox_tladem_catalog.nexus_americas.lmp_realtime t
CROSS JOIN latest l
WHERE t.iso_id = :iso_id
  AND t.interval_datetime >= timestampadd(HOUR, -:hours, l.max_interval_datetime)
GROUP BY t.iso_id, t.interval_datetime
ORDER BY t.interval_datetime;
