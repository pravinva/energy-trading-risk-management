SELECT run_id, exposure_mw, var_95, var_99, expected_shortfall_95, calculated_at
FROM apex.risk.var_results
ORDER BY calculated_at DESC
LIMIT 20;
