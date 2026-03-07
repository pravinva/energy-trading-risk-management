SELECT model_name, mape, rmse, r2, run_timestamp
FROM apex.analytics.model_performance
ORDER BY run_timestamp DESC;
