SELECT from_zone, to_zone, flow_mw, atc_mw, (flow_mw / nullif(atc_mw,0)) * 100 as utilisation_pct
FROM serverless_sandbox_tladem_catalog.nexus_europe.cross_border_flows
WHERE interval_datetime >= current_timestamp() - interval 6 hours
ORDER BY utilisation_pct DESC;
