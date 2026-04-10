-- 7-Day Weather Forecast
-- Used for: Weather impact visualization and correlation analysis

SELECT
    forecast_id,
    region_id,
    forecast_datetime,
    CAST(temperature_celsius AS DOUBLE) AS temperature_celsius,
    CAST(wind_speed_ms AS DOUBLE) AS wind_speed_ms,
    CAST(solar_irradiance_wm2 AS DOUBLE) AS solar_irradiance_wm2,
    CAST(precipitation_mm AS DOUBLE) AS precipitation_mm,
    CAST(humidity_percent AS DOUBLE) AS humidity_percent,
    confidence_level,
    CAST(forecast_horizon_hours AS INT) AS forecast_horizon_hours
FROM apex.forecasting.weather_forecast
WHERE region_id = :region_id
  AND forecast_datetime >= current_timestamp()
  AND forecast_datetime <= current_timestamp() + INTERVAL 7 DAYS
ORDER BY forecast_datetime ASC;
