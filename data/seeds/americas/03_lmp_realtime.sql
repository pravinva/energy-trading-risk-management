DELETE FROM serverless_sandbox_tladem_catalog.nexus_americas.lmp_realtime;
INSERT INTO serverless_sandbox_tladem_catalog.nexus_americas.lmp_realtime
SELECT row_number() OVER (ORDER BY interval_datetime, node_id), node_id, iso_id, interval_datetime,
       cast(lmp as decimal(12,4)), cast(energy_component as decimal(12,4)), cast(congestion_component as decimal(12,4)), cast(loss_component as decimal(12,4)), 'SIMULATED'
FROM (
  SELECT
    m.interval_datetime,
    m.node_id,
    m.iso_id,
    m.lmp,
    greatest(0.5, m.lmp * 0.80) AS energy_component,
    CASE WHEN m.iso_id = 'ERCOT' THEN 0 ELSE greatest(0.0, m.lmp * 0.12) END AS congestion_component,
    CASE WHEN m.iso_id = 'ERCOT' THEN 0 ELSE greatest(0.0, m.lmp * 0.08) END AS loss_component
  FROM (
    SELECT
      t.interval_datetime,
      n.node_id,
      n.iso_id,
      greatest(
        1.0,
        n.node_base
        + n.daily_amp * sin((2 * pi() * ((hour(t.interval_datetime) * 60 + minute(t.interval_datetime)) / 1440.0)) + n.phase_shift)
        + CASE WHEN dayofweek(t.interval_datetime) IN (1, 7) THEN -4.0 ELSE 0.0 END
        + CASE WHEN hour(t.interval_datetime) BETWEEN 17 AND 20 THEN n.peak_bump ELSE 0.0 END
        + (rand() - 0.5) * n.noise_amp
      ) AS lmp
    FROM (SELECT explode(sequence(timestamp'2025-01-01 00:00:00', timestamp'2026-03-01 00:00:00', interval 5 minutes)) as interval_datetime) t
    CROSS JOIN (
      SELECT
        node_id,
        iso_id,
        CASE
          WHEN iso_id = 'ERCOT' THEN 40 + rand() * 20
          WHEN iso_id = 'PJM' THEN 50 + rand() * 24
          WHEN iso_id = 'IESO' THEN 70 + rand() * 28
          ELSE 45 + rand() * 24
        END AS node_base,
        CASE
          WHEN iso_id = 'ERCOT' THEN 8 + rand() * 4
          WHEN iso_id = 'PJM' THEN 9 + rand() * 5
          WHEN iso_id = 'IESO' THEN 11 + rand() * 5
          ELSE 8 + rand() * 4
        END AS daily_amp,
        CASE
          WHEN iso_id = 'ERCOT' THEN 1.25
          WHEN iso_id = 'PJM' THEN 1.05
          WHEN iso_id = 'CAISO' THEN 1.45
          WHEN iso_id = 'IESO' THEN 0.85
          ELSE 1.10
        END AS phase_shift,
        CASE
          WHEN iso_id = 'ERCOT' THEN 6.5
          WHEN iso_id = 'PJM' THEN 5.5
          WHEN iso_id = 'IESO' THEN 7.0
          ELSE 5.0
        END AS peak_bump,
        CASE
          WHEN iso_id = 'ERCOT' THEN 7.0
          WHEN iso_id = 'PJM' THEN 6.0
          WHEN iso_id = 'IESO' THEN 8.0
          ELSE 6.0
        END AS noise_amp
      FROM serverless_sandbox_tladem_catalog.nexus_americas.iso_nodes
    ) n
    WHERE NOT (n.iso_id='IESO' AND t.interval_datetime < timestamp'2025-05-01 00:00:00')
  ) m
) q;
