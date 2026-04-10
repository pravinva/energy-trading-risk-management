-- Production Forecast by Asset Type
-- Used for: Generation mix visualization and capacity planning

SELECT
    forecast_id,
    region_id,
    forecast_datetime,
    asset_type,
    CAST(generation_mw AS DOUBLE) AS generation_mw,
    CAST(capacity_mw AS DOUBLE) AS capacity_mw,
    CAST(efficiency_percent AS DOUBLE) AS efficiency_percent,
    CAST(availability_percent AS DOUBLE) AS availability_percent,
    confidence_level,
    CAST(forecast_horizon_hours AS INT) AS forecast_horizon_hours
FROM apex.forecasting.production_forecast
WHERE region_id = :region_id
  AND forecast_datetime >= current_timestamp()
  AND forecast_datetime <= current_timestamp() + INTERVAL :days DAYS
ORDER BY forecast_datetime ASC, asset_type;
