SELECT asset_id, asset_name, operator, country, fuel_type, capacity_mw, openlink_incumbent
FROM serverless_sandbox_tladem_catalog.nexus_europe.generation_portfolio
WHERE openlink_incumbent = true;
