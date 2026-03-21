-- Weather Impact Correlation Metrics
-- Shows how weather parameters correlate with energy prices

SELECT
    region_id,
    weather_parameter,
    CAST(price_correlation AS DOUBLE) AS price_correlation,
    CAST(price_impact_per_unit AS DOUBLE) AS price_impact_per_unit,
    CAST(volatility_impact AS DOUBLE) AS volatility_impact,
    CAST(sample_size AS INT) AS sample_size,
    last_updated
FROM apex.forecasting.weather_impact
WHERE region_id = :region_id
ORDER BY ABS(price_correlation) DESC;
