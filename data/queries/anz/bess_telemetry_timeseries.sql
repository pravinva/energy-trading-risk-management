SELECT recorded_at, state_of_charge_pct, output_mw, fcas_raise_mw, fcas_lower_mw
FROM serverless_sandbox_tladem_catalog.nexus_anz.bess_telemetry
WHERE duid = :duid
  AND recorded_at >= current_timestamp() - make_interval(0,0,0,0,:hours)
ORDER BY recorded_at;
