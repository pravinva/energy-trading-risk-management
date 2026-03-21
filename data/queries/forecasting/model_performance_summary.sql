-- Model Performance Summary
-- Shows forecasting model accuracy metrics for MLflow tracking

SELECT
    model_id,
    model_name,
    model_type,
    region_id,
    CAST(mape AS DOUBLE) AS mape,
    CAST(mae AS DOUBLE) AS mae,
    CAST(rmse AS DOUBLE) AS rmse,
    CAST(r2_score AS DOUBLE) AS r2_score,
    CAST(bias AS DOUBLE) AS bias,
    evaluation_date,
    algorithm,
    mlflow_run_id
FROM apex.forecasting.model_performance
WHERE (:model_type IS NULL OR model_type = :model_type)
  AND (:region_id IS NULL OR region_id = :region_id)
ORDER BY evaluation_date DESC
LIMIT 100;
