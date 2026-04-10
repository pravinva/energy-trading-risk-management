-- BUY vs SELL Summary Statistics
-- Aggregates volume forecast to show trading recommendations

WITH forecast_data AS (
    SELECT
        region_id,
        forecast_type,
        CAST(volume_mwh AS DOUBLE) AS volume_mwh
    FROM apex.forecasting.volume_forecast
    WHERE region_id = :region_id
      AND forecast_date >= current_date()
      AND forecast_date <= current_date() + INTERVAL 15 DAYS
)
SELECT
    region_id,
    COUNT(*) AS total_days,
    SUM(CASE WHEN forecast_type = 'BUY' THEN 1 ELSE 0 END) AS buy_days,
    SUM(CASE WHEN forecast_type = 'SELL' THEN 1 ELSE 0 END) AS sell_days,
    AVG(volume_mwh) AS avg_volume_mwh,
    SUM(CASE WHEN forecast_type = 'BUY' THEN volume_mwh ELSE 0 END) AS total_buy_volume_mwh,
    SUM(CASE WHEN forecast_type = 'SELL' THEN volume_mwh ELSE 0 END) AS total_sell_volume_mwh
FROM forecast_data
GROUP BY region_id;
