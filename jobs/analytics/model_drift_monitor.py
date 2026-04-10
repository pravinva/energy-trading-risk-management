"""
APEX - Model Drift Monitoring

Monitors ML model performance metrics and triggers retraining alerts when drift detected.
Scheduled to run daily at 8:00 AM UTC.

Drift Detection:
- MAPE (Mean Absolute Percentage Error) threshold monitoring
- R² score degradation detection
- Prediction vs actual comparison
- Automatic retraining alerts
"""

import argparse
from datetime import datetime, date, timedelta
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, avg, max as spark_max, min as spark_min, current_timestamp, lit


def check_model_performance(spark, catalog: str, model_type: str, mape_threshold: float, r2_threshold: float):
    """
    Check model performance metrics for drift

    Args:
        spark: SparkSession
        catalog: Unity Catalog name
        model_type: 'PRICE' or 'DEMAND'
        mape_threshold: MAPE threshold (e.g., 15.0 for 15%)
        r2_threshold: Minimum acceptable R² score (e.g., 0.85)

    Returns:
        dict with drift detection results
    """
    print(f"Checking {model_type} model performance...")

    # Load model performance metrics from last 30 days
    lookback_date = (date.today() - timedelta(days=30)).isoformat()

    performance_query = f"""
        SELECT
            model_id,
            model_name,
            model_type,
            region_id,
            mape,
            mae,
            rmse,
            r2_score,
            evaluation_date,
            mlflow_run_id
        FROM {catalog}.forecasting.model_performance
        WHERE model_type = '{model_type}'
          AND evaluation_date >= '{lookback_date}'
        ORDER BY evaluation_date DESC
    """

    try:
        performance_df = spark.sql(performance_query)
        record_count = performance_df.count()

        if record_count == 0:
            print(f"No performance records found for {model_type} models")
            return None

        print(f"Found {record_count} performance records")

        # Calculate aggregated metrics
        metrics_agg = performance_df.agg(
            avg("mape").alias("avg_mape"),
            avg("r2_score").alias("avg_r2"),
            spark_max("mape").alias("max_mape"),
            spark_min("r2_score").alias("min_r2")
        ).collect()[0]

        avg_mape = metrics_agg['avg_mape'] if metrics_agg['avg_mape'] else 0.0
        avg_r2 = metrics_agg['avg_r2'] if metrics_agg['avg_r2'] else 1.0
        max_mape = metrics_agg['max_mape'] if metrics_agg['max_mape'] else 0.0
        min_r2 = metrics_agg['min_r2'] if metrics_agg['min_r2'] else 1.0

        print(f"\n{model_type} Model Performance (Last 30 Days):")
        print(f"  Average MAPE: {avg_mape:.2f}%")
        print(f"  Average R²:   {avg_r2:.4f}")
        print(f"  Max MAPE:     {max_mape:.2f}%")
        print(f"  Min R²:       {min_r2:.4f}")

        # Detect drift
        drift_detected = False
        drift_reasons = []

        if avg_mape > mape_threshold:
            drift_detected = True
            drift_reasons.append(f"Average MAPE {avg_mape:.2f}% exceeds threshold {mape_threshold:.2f}%")

        if avg_r2 < r2_threshold:
            drift_detected = True
            drift_reasons.append(f"Average R² {avg_r2:.4f} below threshold {r2_threshold:.4f}")

        if drift_detected:
            print(f"\n⚠️  MODEL DRIFT DETECTED for {model_type}")
            for reason in drift_reasons:
                print(f"    - {reason}")
        else:
            print(f"\n✓ No drift detected for {model_type} models")

        return {
            'model_type': model_type,
            'avg_mape': avg_mape,
            'avg_r2': avg_r2,
            'max_mape': max_mape,
            'min_r2': min_r2,
            'drift_detected': drift_detected,
            'drift_reasons': drift_reasons,
            'record_count': record_count
        }

    except Exception as e:
        print(f"Error checking {model_type} model performance: {str(e)}")
        return None


def main(catalog: str, mape_threshold: float = 15.0, r2_threshold: float = 0.85):
    """
    Main function for model drift monitoring

    Args:
        catalog: Unity Catalog name
        mape_threshold: MAPE threshold percentage
        r2_threshold: Minimum acceptable R² score
    """
    spark = SparkSession.builder.appName("APEX-Model-Drift-Monitor").getOrCreate()

    print("=" * 80)
    print("APEX - MODEL DRIFT MONITORING")
    print("=" * 80)
    print(f"Catalog: {catalog}")
    print(f"MAPE Threshold: {mape_threshold}%")
    print(f"R² Threshold: {r2_threshold}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()

    try:
        # Check price models
        price_results = check_model_performance(
            spark, catalog, "PRICE", mape_threshold, r2_threshold
        )

        print("\n" + "-" * 80 + "\n")

        # Check demand models
        demand_results = check_model_performance(
            spark, catalog, "DEMAND", mape_threshold, r2_threshold
        )

        # Save drift monitoring results
        print("\nSaving drift monitoring results...")
        monitoring_data = []

        if price_results:
            monitoring_data.append((
                datetime.now(),
                date.today().isoformat(),
                price_results['model_type'],
                price_results['avg_mape'],
                price_results['avg_r2'],
                price_results['max_mape'],
                price_results['min_r2'],
                price_results['drift_detected'],
                '; '.join(price_results['drift_reasons']) if price_results['drift_reasons'] else None,
                price_results['record_count']
            ))

        if demand_results:
            monitoring_data.append((
                datetime.now(),
                date.today().isoformat(),
                demand_results['model_type'],
                demand_results['avg_mape'],
                demand_results['avg_r2'],
                demand_results['max_mape'],
                demand_results['min_r2'],
                demand_results['drift_detected'],
                '; '.join(demand_results['drift_reasons']) if demand_results['drift_reasons'] else None,
                demand_results['record_count']
            ))

        if monitoring_data:
            schema = ["monitoring_timestamp", "monitoring_date", "model_type", "avg_mape", "avg_r2",
                     "max_mape", "min_r2", "drift_detected", "drift_reasons", "records_evaluated"]

            monitoring_df = spark.createDataFrame(monitoring_data, schema)

            monitoring_table = f"{catalog}.forecasting.drift_monitoring"
            monitoring_df.write.format("delta").mode("append").saveAsTable(monitoring_table)
            print(f"✓ Saved monitoring results to {monitoring_table}")

        # Log alerts for models with drift
        drift_alerts = []

        if price_results and price_results['drift_detected']:
            drift_alerts.append((
                datetime.now(),
                "MODEL_DRIFT",
                f"PRICE model drift detected: {'; '.join(price_results['drift_reasons'])}",
                "HIGH"
            ))

        if demand_results and demand_results['drift_detected']:
            drift_alerts.append((
                datetime.now(),
                "MODEL_DRIFT",
                f"DEMAND model drift detected: {'; '.join(demand_results['drift_reasons'])}",
                "HIGH"
            ))

        if drift_alerts:
            alert_df = spark.createDataFrame(
                drift_alerts,
                ["timestamp", "alert_type", "message", "severity"]
            )

            alert_table = f"{catalog}.forecasting.model_alerts"
            alert_df.write.format("delta").mode("append").saveAsTable(alert_table)
            print(f"\n⚠️  Logged {len(drift_alerts)} drift alerts to {alert_table}")
            print("    Consider triggering model retraining workflow")

        print("\n" + "=" * 80)
        print("MODEL DRIFT MONITORING COMPLETE")
        if price_results and demand_results:
            total_drift = (price_results['drift_detected'] or demand_results['drift_detected'])
            print(f"Status: {'⚠️  DRIFT DETECTED' if total_drift else '✓ ALL MODELS HEALTHY'}")
        print("=" * 80)

    except Exception as e:
        print(f"❌ Error during drift monitoring: {str(e)}")
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="APEX Model Drift Monitoring")
    parser.add_argument("--catalog", type=str, required=True, help="Unity Catalog name")
    parser.add_argument("--mape-threshold", type=float, default=15.0, help="MAPE threshold percentage")
    parser.add_argument("--r2-threshold", type=float, default=0.85, help="Minimum R² threshold")

    args = parser.parse_args()
    main(args.catalog, args.mape_threshold, args.r2_threshold)
