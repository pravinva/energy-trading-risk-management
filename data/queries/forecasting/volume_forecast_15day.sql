-- 15-Day BUY/SELL Volume Forecast
-- KEY FEATURE: Daily trading volume recommendations based on weather, maintenance, and market factors
-- Used for: Volume Forecast visualization in Quant Console

SELECT
    forecast_id,
    region_id,
    forecast_date,
    forecast_type,
    CAST(volume_mwh AS DOUBLE) AS volume_mwh,
    CAST(base_volume_mwh AS DOUBLE) AS base_volume_mwh,
    CAST(weather_impact_pct AS DOUBLE) AS weather_impact_pct,
    CAST(maintenance_impact_pct AS DOUBLE) AS maintenance_impact_pct,
    CAST(outage_impact_pct AS DOUBLE) AS outage_impact_pct,
    CAST(market_demand_factor AS DOUBLE) AS market_demand_factor,
    confidence_level
FROM apex.forecasting.volume_forecast
WHERE region_id = :region_id
  AND forecast_date >= current_date()
  AND forecast_date <= current_date() + INTERVAL 15 DAYS
ORDER BY forecast_date ASC;
