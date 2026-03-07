"""
APEX fresh DLT pipeline.
Compact bronze/silver/gold implementation for ETRM ingestion.
"""

import dlt
from pyspark.sql import functions as F


@dlt.table(name="bronze_etrm_trades", comment="Raw ETRM landing")
def bronze_etrm_trades():
    return spark.readStream.table("apex_fresh.ingestion.raw_etrm_trades")


@dlt.table(name="silver_trades", comment="Validated parsed trades")
@dlt.expect_or_drop("valid_market", "market IN ('NEM','EPEX','ERCOT')")
def silver_trades():
    return dlt.read_stream("bronze_etrm_trades").select(
        F.get_json_object("payload", "$.trade_id").alias("trade_id"),
        F.col("market"),
        F.get_json_object("payload", "$.instrument_id").alias("instrument_id"),
        F.get_json_object("payload", "$.trader_id").alias("trader_id"),
        F.get_json_object("payload", "$.direction").alias("direction"),
        F.get_json_object("payload", "$.volume_mw").cast("decimal(10,2)").alias("volume_mw"),
        F.get_json_object("payload", "$.price").cast("decimal(12,4)").alias("price"),
        F.col("source_system"),
        F.col("received_at").alias("ingested_at"),
    )


@dlt.table(name="gold_positions", comment="Net positions by instrument")
def gold_positions():
    trades = dlt.read("silver_trades")
    return trades.groupBy("market", "instrument_id", "trader_id").agg(
        F.sum(
            F.when(F.col("direction") == "BUY", F.col("volume_mw"))
            .otherwise(-F.col("volume_mw"))
        ).alias("net_volume_mw"),
        F.avg("price").alias("avg_price"),
        F.max("ingested_at").alias("last_sync_at"),
    )

