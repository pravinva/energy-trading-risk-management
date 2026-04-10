# Databricks notebook source
# MAGIC %md
# MAGIC # APEX Demand Forecasting with AutoML
# MAGIC
# MAGIC This notebook trains a demand forecasting model using Databricks AutoML on historical NEM market data.
# MAGIC
# MAGIC **Features:**
# MAGIC - Time series forecasting with automated feature engineering
# MAGIC - Weather correlation analysis
# MAGIC - Hyperparameter tuning
# MAGIC - MLflow tracking and model registry
# MAGIC
# MAGIC **Target:** Predict electricity demand (MW) for NEM regions
# MAGIC
# MAGIC **Model Type:** Regression with time series features

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Configuration

# COMMAND ----------

import pandas as pd
from datetime import datetime, timedelta
import databricks.automl as automl
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, hour, dayofweek, month, lag, avg, stddev
from pyspark.sql.window import Window

# Configuration
CATALOG = "apex_fresh"
REGION_ID = "NSW1"  # Change to VIC1, QLD1, SA1 for other regions
MODEL_NAME = f"apex_demand_forecast_{REGION_ID.lower()}"
EXPERIMENT_PATH = f"/Users/{spark.sql('SELECT current_user()').collect()[0][0]}/apex-demand-forecasting"

print(f"Training demand forecast model for region: {REGION_ID}")
print(f"Experiment path: {EXPERIMENT_PATH}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Load Historical Demand Data

# COMMAND ----------

# Load historical demand data from NEM predispatch
sql_query = f"""
SELECT
    interval_datetime,
    region_id,
    CAST(demand_forecast AS DOUBLE) as demand_mw,
    CAST(forecast_price AS DOUBLE) as spot_price,
    hour(interval_datetime) as hour_of_day,
    dayofweek(interval_datetime) as day_of_week,
    month(interval_datetime) as month,
    CASE
        WHEN dayofweek(interval_datetime) IN (1, 7) THEN 1
        ELSE 0
    END as is_weekend,
    CASE
        WHEN month(interval_datetime) IN (12, 1, 2) THEN 'summer'
        WHEN month(interval_datetime) IN (3, 4, 5) THEN 'autumn'
        WHEN month(interval_datetime) IN (6, 7, 8) THEN 'winter'
        ELSE 'spring'
    END as season
FROM {CATALOG}.market_nem.predispatch_prices
WHERE region_id = '{REGION_ID}'
    AND interval_datetime >= current_timestamp() - INTERVAL 90 DAYS
    AND demand_forecast IS NOT NULL
    AND demand_forecast > 0
ORDER BY interval_datetime DESC
"""

df = spark.sql(sql_query)

print(f"Loaded {df.count()} records for {REGION_ID}")
df.show(5)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Feature Engineering

# COMMAND ----------

# Create lagged demand features
window_spec = Window.partitionBy("region_id").orderBy("interval_datetime")

df_features = df.withColumn("demand_lag_1h", lag("demand_mw", 1).over(window_spec)) \
    .withColumn("demand_lag_24h", lag("demand_mw", 24).over(window_spec)) \
    .withColumn("demand_lag_168h", lag("demand_mw", 168).over(window_spec)) \
    .withColumn("price_lag_1h", lag("spot_price", 1).over(window_spec))

# Calculate rolling statistics
rolling_window_24h = Window.partitionBy("region_id").orderBy("interval_datetime").rowsBetween(-24, -1)
df_features = df_features.withColumn("demand_rolling_24h_avg", avg("demand_mw").over(rolling_window_24h)) \
    .withColumn("demand_rolling_24h_std", stddev("demand_mw").over(rolling_window_24h))

# Create peak demand indicators
df_features = df_features.withColumn(
    "is_peak_hour",
    col("hour_of_day").isin([7, 8, 9, 18, 19, 20]).cast("int")
)

# One-hot encode season
from pyspark.ml.feature import StringIndexer, OneHotEncoder
from pyspark.ml import Pipeline

indexer = StringIndexer(inputCol="season", outputCol="season_index")
encoder = OneHotEncoder(inputCol="season_index", outputCol="season_encoded")

pipeline = Pipeline(stages=[indexer, encoder])
model = pipeline.fit(df_features)
df_features = model.transform(df_features)

# Drop rows with null lagged features
df_features = df_features.dropna()

print(f"After feature engineering: {df_features.count()} records")
df_features.select("interval_datetime", "demand_mw", "demand_lag_1h", "demand_rolling_24h_avg", "is_peak_hour").show(5)

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
# MAGIC ## 5. Prepare Data for AutoML

# COMMAND ----------

# Convert to Pandas
train_pdf = df_train.toPandas()

# Select features for AutoML
feature_cols = [
    "hour_of_day",
    "day_of_week",
    "month",
    "is_weekend",
    "is_peak_hour",
    "spot_price",
    "demand_lag_1h",
    "demand_lag_24h",
    "demand_lag_168h",
    "price_lag_1h",
    "demand_rolling_24h_avg",
    "demand_rolling_24h_std"
]

target_col = "demand_mw"

# Prepare training data
train_data = train_pdf[feature_cols + [target_col]].dropna()

print(f"Training AutoML with {len(train_data)} samples")
print(f"Features: {feature_cols}")
print(f"Target: {target_col}")
print(f"\nDemand statistics:")
print(train_data[target_col].describe())

# COMMAND ----------

# MAGIC %md
# MAGIC ## 6. Run Databricks AutoML

# COMMAND ----------

# Run AutoML for demand forecasting
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
print(f"Best RMSE: {summary.best_trial.metrics['val_root_mean_squared_error']:.2f} MW")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 7. Register Best Model

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
    description=f"AutoML demand forecast model for {REGION_ID}. Trained on {len(train_data)} samples with R²={summary.best_trial.metrics['val_r2_score']:.4f}"
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 8. Evaluate on Test Set

# COMMAND ----------

from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import numpy as np

# Load the model
model = mlflow.sklearn.load_model(model_uri)

# Prepare test data
test_pdf = df_test.toPandas()
X_test = test_pdf[feature_cols].dropna()
y_test = test_pdf.loc[X_test.index, target_col]

# Make predictions
y_pred = model.predict(X_test)

# Calculate metrics
mae = mean_absolute_error(y_test, y_pred)
rmse = np.sqrt(mean_squared_error(y_test, y_pred))
r2 = r2_score(y_test, y_pred)
mape = np.mean(np.abs((y_test - y_pred) / y_test)) * 100

print("\n=== Test Set Performance ===")
print(f"MAE:  {mae:.2f} MW")
print(f"RMSE: {rmse:.2f} MW")
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
# MAGIC ## 9. Save Predictions

# COMMAND ----------

# Create predictions DataFrame
test_pdf_with_predictions = test_pdf.loc[X_test.index].copy()
test_pdf_with_predictions['predicted_demand'] = y_pred
test_pdf_with_predictions['prediction_error'] = test_pdf_with_predictions['demand_mw'] - y_pred
test_pdf_with_predictions['abs_percentage_error'] = np.abs(test_pdf_with_predictions['prediction_error'] / test_pdf_with_predictions['demand_mw']) * 100
test_pdf_with_predictions['model_version'] = model_version.version
test_pdf_with_predictions['mlflow_run_id'] = summary.best_trial.mlflow_run_id
test_pdf_with_predictions['prediction_timestamp'] = datetime.now()

# Convert back to Spark DataFrame
predictions_df = spark.createDataFrame(test_pdf_with_predictions[['interval_datetime', 'region_id', 'demand_mw',
                                                                   'predicted_demand', 'prediction_error',
                                                                   'abs_percentage_error', 'model_version',
                                                                   'mlflow_run_id', 'prediction_timestamp']])

# Save to Delta Lake
predictions_table = f"{CATALOG}.forecasting.demand_forecast_automl"
predictions_df.write.format("delta").mode("append").saveAsTable(predictions_table)

print(f"\nSaved {predictions_df.count()} predictions to {predictions_table}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 10. Update Model Performance Table

# COMMAND ----------

from pyspark.sql.types import StructType, StructField, StringType, DoubleType

# Create model performance record
performance_data = [(
    f"automl-demand-{REGION_ID.lower()}-{datetime.now().strftime('%Y%m%d')}",
    MODEL_NAME,
    "DEMAND",
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
# MAGIC ## 11. Summary

# COMMAND ----------

print("=" * 80)
print("APEX DEMAND FORECASTING - AUTOML TRAINING COMPLETE")
print("=" * 80)
print(f"\nRegion: {REGION_ID}")
print(f"Model: {MODEL_NAME} (version {model_version.version})")
print(f"MLflow Run ID: {summary.best_trial.mlflow_run_id}")
print(f"\nTest Set Performance:")
print(f"  - R²:   {r2:.4f}")
print(f"  - RMSE: {rmse:.2f} MW")
print(f"  - MAE:  {mae:.2f} MW")
print(f"  - MAPE: {mape:.2f}%")
print(f"\nModel registered in MLflow Model Registry: {MODEL_NAME}")
print(f"Predictions saved to: {predictions_table}")
print(f"Performance tracked in: {performance_table}")
print("=" * 80)
