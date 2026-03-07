SELECT delivery_year, clearing_price_mw_day, total_cost_billions, data_center_cost_pct, price_cap_hit, reliability_shortfall_mw,
       clearing_price_mw_day * 365 as capacity_cost_per_mw_per_year
FROM serverless_sandbox_tladem_catalog.nexus_americas.pjm_capacity_auctions
ORDER BY delivery_year;
