-- Generation Mix Historical Trend
-- Shows how the generation mix has evolved over time

SELECT
    region_id,
    reading_datetime,
    asset_type,
    CAST(generation_mw AS DOUBLE) AS generation_mw,
    CAST(total_generation_mw AS DOUBLE) AS total_generation_mw,
    CAST(mix_percentage AS DOUBLE) AS mix_percentage
FROM apex.forecasting.generation_mix_historical
WHERE region_id = :region_id
  AND reading_datetime >= current_timestamp() - INTERVAL :hours HOURS
ORDER BY reading_datetime DESC, asset_type;
