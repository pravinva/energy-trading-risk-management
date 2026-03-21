-- Plant Status Timeline (for Gantt Chart)
-- Shows outages, maintenance, and ramp events across all plants in a region

SELECT
    event_id,
    plant_name,
    plant_type,
    region_id,
    event_type,
    start_datetime,
    end_datetime,
    CAST(capacity_impact_mw AS DOUBLE) AS capacity_impact_mw,
    grid_impact,
    description,
    status
FROM apex.forecasting.plant_status
WHERE region_id = :region_id
  AND start_datetime <= current_timestamp() + INTERVAL :days DAYS
  AND end_datetime >= current_timestamp()
ORDER BY start_datetime ASC, plant_name;
