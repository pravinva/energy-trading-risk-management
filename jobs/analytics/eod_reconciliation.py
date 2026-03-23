"""
APEX - End of Day Reconciliation

Reconciles internal trade records against external settlement data.
Scheduled to run daily at 5:00 PM UTC.

Reconciliation Checks:
- Trade volume matching
- Price validation
- Settlement confirmation
- Discrepancy flagging
"""

import argparse
from datetime import datetime, date, timedelta
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, abs as spark_abs, when, lit, current_timestamp


def reconcile_trades(spark, catalog: str, reconciliation_date: date):
    """
    Reconcile trades against settlement data

    Args:
        spark: SparkSession
        catalog: Unity Catalog name
        reconciliation_date: Date to reconcile
    """
    print(f"Reconciling trades for date: {reconciliation_date}")

    # Load today's trades
    trades_query = f"""
        SELECT
            trade_id,
            timestamp,
            instrument,
            direction,
            volume_mw,
            price,
            counterparty,
            status,
            DATE(timestamp) as trade_date
        FROM {catalog}.trading.trades
        WHERE DATE(timestamp) = '{reconciliation_date}'
    """

    trades_df = spark.sql(trades_query)
    trade_count = trades_df.count()
    print(f"Found {trade_count} trades to reconcile")

    if trade_count == 0:
        print("No trades to reconcile for this date")
        return

    # Simulate settlement data (in production, this would come from external source)
    # For demo purposes, we'll create settlement records with small variations
    print("Loading settlement data...")

    # In production, this would load from external settlement system
    # For now, we'll use the trade data with small random variations to simulate discrepancies
    settlement_df = trades_df.selectExpr(
        "trade_id as settlement_id",
        "trade_id",
        "volume_mw as settlement_volume",
        "price as settlement_price",
        "CASE WHEN rand() < 0.05 THEN 'DISCREPANCY' ELSE 'MATCHED' END as settlement_status"
    )

    # Join trades with settlement
    print("Matching trades with settlement...")
    reconciliation_df = trades_df.join(
        settlement_df,
        trades_df.trade_id == settlement_df.trade_id,
        "left"
    )

    # Calculate discrepancies
    reconciliation_df = reconciliation_df.withColumn(
        "volume_diff",
        spark_abs(col("volume_mw") - col("settlement_volume"))
    ).withColumn(
        "price_diff",
        spark_abs(col("price") - col("settlement_price"))
    ).withColumn(
        "has_discrepancy",
        when(
            (col("settlement_status") == "DISCREPANCY") |
            (col("volume_diff") > 0.01) |
            (col("price_diff") > 0.01),
            True
        ).otherwise(False)
    )

    # Count discrepancies
    total_trades = reconciliation_df.count()
    discrepancies = reconciliation_df.filter(col("has_discrepancy") == True).count()
    matched_trades = total_trades - discrepancies

    print(f"\nReconciliation Summary:")
    print(f"  Total Trades:    {total_trades}")
    print(f"  Matched:         {matched_trades}")
    print(f"  Discrepancies:   {discrepancies}")

    # Save reconciliation results
    print("\nSaving reconciliation results...")
    recon_results = reconciliation_df.select(
        "trade_id",
        "trade_date",
        "instrument",
        "volume_mw",
        "settlement_volume",
        "volume_diff",
        "price",
        "settlement_price",
        "price_diff",
        "has_discrepancy",
        current_timestamp().alias("reconciliation_timestamp")
    )

    recon_table = f"{catalog}.trading.reconciliation_results"
    recon_results.write.format("delta").mode("append").saveAsTable(recon_table)
    print(f"✓ Saved {total_trades} reconciliation results to {recon_table}")

    # Flag discrepancies for review
    if discrepancies > 0:
        print(f"\n⚠️  {discrepancies} discrepancies found!")

        discrepancy_df = reconciliation_df.filter(col("has_discrepancy") == True)

        # Log alerts for discrepancies
        alerts_data = discrepancy_df.select(
            current_timestamp().alias("timestamp"),
            lit("TRADE_DISCREPANCY").alias("alert_type"),
            col("trade_id"),
            col("instrument"),
            col("volume_diff"),
            col("price_diff"),
            lit("MEDIUM").alias("severity")
        )

        alert_table = f"{catalog}.trading.reconciliation_alerts"
        alerts_data.write.format("delta").mode("append").saveAsTable(alert_table)
        print(f"✓ Logged {discrepancies} alerts to {alert_table}")

        # Show sample discrepancies
        print("\nSample Discrepancies:")
        discrepancy_df.select("trade_id", "instrument", "volume_diff", "price_diff").show(5, truncate=False)

    return {
        'total_trades': total_trades,
        'matched': matched_trades,
        'discrepancies': discrepancies,
        'match_rate': (matched_trades / total_trades * 100) if total_trades > 0 else 100.0
    }


def main(catalog: str):
    """
    Main function for end-of-day reconciliation

    Args:
        catalog: Unity Catalog name
    """
    spark = SparkSession.builder.appName("APEX-EOD-Reconciliation").getOrCreate()

    print("=" * 80)
    print("APEX - END OF DAY RECONCILIATION")
    print("=" * 80)
    print(f"Catalog: {catalog}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()

    # Reconcile today's trades
    today = date.today()

    try:
        results = reconcile_trades(spark, catalog, today)

        if results:
            # Save summary
            summary_data = [(
                datetime.now(),
                today.isoformat(),
                results['total_trades'],
                results['matched'],
                results['discrepancies'],
                results['match_rate']
            )]

            summary_df = spark.createDataFrame(
                summary_data,
                ["reconciliation_timestamp", "trade_date", "total_trades", "matched", "discrepancies", "match_rate"]
            )

            summary_table = f"{catalog}.trading.reconciliation_summary"
            summary_df.write.format("delta").mode("append").saveAsTable(summary_table)
            print(f"\n✓ Saved reconciliation summary to {summary_table}")

        print("\n" + "=" * 80)
        print("END OF DAY RECONCILIATION COMPLETE")
        print(f"Match Rate: {results['match_rate']:.2f}%")
        print("=" * 80)

    except Exception as e:
        print(f"❌ Error during reconciliation: {str(e)}")
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="APEX End of Day Reconciliation")
    parser.add_argument("--catalog", type=str, required=True, help="Unity Catalog name")

    args = parser.parse_args()
    main(args.catalog)
