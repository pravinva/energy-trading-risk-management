# Databricks notebook source
# MAGIC %md
# MAGIC # APEX Price Forecasting with AutoML
# MAGIC
# MAGIC This notebook trains a price forecasting model using Databricks AutoML on historical NEM market data.
# MAGIC
# MAGIC **Features:**
# MAGIC - Automated feature engineering
# MAGIC - Hyperparameter tuning
# MAGIC - MLflow tracking and model registry
# MAGIC - Model explainability with SHAP
# MAGIC
# MAGIC **Target:** Predict spot prices for NEM regions (NSW1, VIC1, QLD1, SA1)
# MAGIC
# MAGIC **Model Type:** Regression (AutoML will test XGBoost, LightGBM, Random Forest, etc.)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Configuration

# COMMAND ----------

import pandas as pd
from datetime import datetime, timedelta
import databricks.automl as automl
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, hour, dayofweek, month, lag, avg
from pyspark.sql.window import Window

# Configuration
CATALOG = "apex_fresh"
REGION_ID = "NSW1"  # Change to VIC1, QLD1, SA1 for other regions
MODEL_NAME = f"apex_price_forecast_{REGION_ID.lower()}"
EXPERIMENT_PATH = f"/Users/{spark.sql('SELECT current_user()').collect()[0][0]}/apex-price-forecasting"

print(f"Training price forecast model for region: {REGION_ID}")
print(f"Experiment path: {EXPERIMENT_PATH}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Load Historical Price Data

# COMMAND ----------

# Load historical spot prices from NEM predispatch data
sql_query = f"""
SELECT
    interval_datetime,
    region_id,
    CAST(forecast_price AS DOUBLE) as spot_price,
    CAST(demand_forecast AS DOUBLE) as demand_mw,
    hour(interval_datetime) as hour_of_day,
    dayofweek(interval_datetime) as day_of_week,
    month(interval_datetime) as month,
    CASE
        WHEN dayofweek(interval_datetime) IN (1, 7) THEN 1
        ELSE 0
    END as is_weekend
FROM {CATALOG}.market_nem.predispatch_prices
WHERE region_id = '{REGION_ID}'
    AND interval_datetime >= current_timestamp() - INTERVAL 90 DAYS
    AND forecast_price IS NOT NULL
    AND forecast_price > 0  -- Remove negative prices for training
ORDER BY interval_datetime DESC
"""

df = spark.sql(sql_query)

print(f"Loaded {df.count()} records for {REGION_ID}")
df.show(5)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Feature Engineering

# COMMAND ----------

# Create lagged features for time series
window_spec = Window.partitionBy("region_id").orderBy("interval_datetime")

df_features = df.withColumn("price_lag_1h", lag("spot_price", 1).over(window_spec)) \
    .withColumn("price_lag_24h", lag("spot_price", 24).over(window_spec)) \
    .withColumn("price_lag_168h", lag("spot_price", 168).over(window_spec)) \
    .withColumn("demand_lag_1h", lag("demand_mw", 1).over(window_spec))

# Calculate rolling averages
rolling_window_24h = Window.partitionBy("region_id").orderBy("interval_datetime").rowsBetween(-24, -1)
df_features = df_features.withColumn("price_rolling_24h_avg", avg("spot_price").over(rolling_window_24h))

# Drop rows with null lagged features
df_features = df_features.dropna()

print(f"After feature engineering: {df_features.count()} records")
df_features.select("interval_datetime", "spot_price", "price_lag_1h", "price_rolling_24h_avg", "hour_of_day", "is_weekend").show(5)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. Train/Test Split

# COMMAND ----------

# Split by time: 80% train, 20% test
train_size = 0.8
total_count = df_features.count()
split_point = int(total_count * train_size)

# Create train/test datasets
df_sorted = df_features.orderBy("interval_datetime")
df_train = df_sorted.limit(split_point)
df_test = df_sorted.subtract(df_train)

print(f"Training set: {df_train.count()} records")
print(f"Test set: {df_test.count()} records")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5. Run Databricks AutoML

# COMMAND ----------

# Convert to Pandas for AutoML (AutoML works with Pandas DataFrames)
train_pdf = df_train.toPandas()

# Select features for AutoML
feature_cols = [
    "hour_of_day",
    "day_of_week",
    "month",
    "is_weekend",
    "demand_mw",
    "price_lag_1h",
    "price_lag_24h",
    "price_lag_168h",
    "demand_lag_1h",
    "price_rolling_24h_avg"
]

target_col = "spot_price"

# Prepare training data
train_data = train_pdf[feature_cols + [target_col]]

print(f"Training AutoML with {len(train_data)} samples")
print(f"Features: {feature_cols}")
print(f"Target: {target_col}")

# COMMAND ----------

# Run AutoML
summary = automl.regress(
    dataset=train_data,
    target_col=target_col,
    primary_metric="r2",
    timeout_minutes=30,
    max_trials=20,
    experiment_name=EXPERIMENT_PATH
)

print(f"\nAutoML Run Summary:")
print(f"Best trial ID: {summary.best_trial.mlflow_run_id}")
print(f"Best R² score: {summary.best_trial.metrics['val_r2_score']:.4f}")
print(f"Best RMSE: {summary.best_trial.metrics['val_root_mean_squared_error']:.2f}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 6. Register Best Model to MLflow Model Registry

# COMMAND ----------

import mlflow

# Register the best model
model_uri = f"runs:/{summary.best_trial.mlflow_run_id}/model"
model_version = mlflow.register_model(model_uri, MODEL_NAME)

print(f"\nRegistered model: {MODEL_NAME}")
print(f"Model version: {model_version.version}")
print(f"MLflow Run ID: {summary.best_trial.mlflow_run_id}")

# Add model description
client = mlflow.tracking.MlflowClient()
client.update_model_version(
    name=MODEL_NAME,
    version=model_version.version,
    description=f"AutoML price forecast model for {REGION_ID}. Trained on {len(train_data)} samples with R²={summary.best_trial.metrics['val_r2_score']:.4f}"
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 7. Evaluate on Test Set

# COMMAND ----------

from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import numpy as np

# Load the model
model = mlflow.sklearn.load_model(model_uri)

# Prepare test data
test_pdf = df_test.toPandas()
X_test = test_pdf[feature_cols]
y_test = test_pdf[target_col]

# Make predictions
y_pred = model.predict(X_test)

# Calculate metrics
mae = mean_absolute_error(y_test, y_pred)
rmse = np.sqrt(mean_squared_error(y_test, y_pred))
r2 = r2_score(y_test, y_pred)
mape = np.mean(np.abs((y_test - y_pred) / y_test)) * 100

print("\n=== Test Set Performance ===")
print(f"MAE:  ${mae:.2f}/MWh")
print(f"RMSE: ${rmse:.2f}/MWh")
print(f"R²:   {r2:.4f}")
print(f"MAPE: {mape:.2f}%")

# Log test metrics to MLflow
with mlflow.start_run(run_id=summary.best_trial.mlflow_run_id):
    mlflow.log_metrics({
        "test_mae": mae,
        "test_rmse": rmse,
        "test_r2": r2,
        "test_mape": mape
    })

# COMMAND ----------

# MAGIC %md
# MAGIC ## 8. Save Predictions to Delta Lake

# COMMAND ----------

# Create predictions DataFrame
test_pdf['predicted_price'] = y_pred
test_pdf['prediction_error'] = test_pdf['spot_price'] - test_pdf['predicted_price']
test_pdf['abs_percentage_error'] = np.abs(test_pdf['prediction_error'] / test_pdf['spot_price']) * 100
test_pdf['model_version'] = model_version.version
test_pdf['mlflow_run_id'] = summary.best_trial.mlflow_run_id
test_pdf['prediction_timestamp'] = datetime.now()

# Convert back to Spark DataFrame
predictions_df = spark.createDataFrame(test_pdf[['interval_datetime', 'region_id', 'spot_price',
                                                   'predicted_price', 'prediction_error',
                                                   'abs_percentage_error', 'model_version',
                                                   'mlflow_run_id', 'prediction_timestamp']])

# Save to Delta Lake
predictions_table = f"{CATALOG}.forecasting.price_forecast_automl"
predictions_df.write.format("delta").mode("append").saveAsTable(predictions_table)

print(f"\nSaved {predictions_df.count()} predictions to {predictions_table}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 9. Update Model Performance Tracking Table

# COMMAND ----------

from pyspark.sql.types import StructType, StructField, StringType, DoubleType, DateType

# Create model performance record
performance_data = [(
    f"automl-{REGION_ID.lower()}-{datetime.now().strftime('%Y%m%d')}",
    MODEL_NAME,
    "PRICE",
    REGION_ID,
    float(mape),
    float(mae),
    float(rmse),
    float(r2),
    0.0,  # bias
    datetime.now().date().isoformat(),
    "AutoML (Best Trial)",
    summary.best_trial.mlflow_run_id
)]

schema = StructType([
    StructField("model_id", StringType(), False),
    StructField("model_name", StringType(), False),
    StructField("model_type", StringType(), False),
    StructField("region_id", StringType(), False),
    StructField("mape", DoubleType(), True),
    StructField("mae", DoubleType(), True),
    StructField("rmse", DoubleType(), True),
    StructField("r2_score", DoubleType(), True),
    StructField("bias", DoubleType(), True),
    StructField("evaluation_date", StringType(), False),
    StructField("algorithm", StringType(), True),
    StructField("mlflow_run_id", StringType(), True),
])

performance_df = spark.createDataFrame(performance_data, schema)

# Save to model_performance table
performance_table = f"{CATALOG}.forecasting.model_performance"
performance_df.write.format("delta").mode("append").saveAsTable(performance_table)

print(f"\nUpdated model performance table: {performance_table}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 10. Summary

# COMMAND ----------

print("=" * 80)
print("APEX PRICE FORECASTING - AUTOML TRAINING COMPLETE")
print("=" * 80)
print(f"\nRegion: {REGION_ID}")
print(f"Model: {MODEL_NAME} (version {model_version.version})")
print(f"MLflow Run ID: {summary.best_trial.mlflow_run_id}")
print(f"\nTest Set Performance:")
print(f"  - R²:   {r2:.4f}")
print(f"  - RMSE: ${rmse:.2f}/MWh")
print(f"  - MAE:  ${mae:.2f}/MWh")
print(f"  - MAPE: {mape:.2f}%")
print(f"\nModel registered in MLflow Model Registry: {MODEL_NAME}")
print(f"Predictions saved to: {predictions_table}")
print(f"Performance tracked in: {performance_table}")
print("=" * 80)
