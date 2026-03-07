# Databricks notebook source
import math
import hashlib
from datetime import datetime, timezone

import mlflow
import numpy as np
import pandas as pd
from pyspark.sql import functions as F
from sklearn.metrics import mean_absolute_percentage_error, mean_squared_error, r2_score
from xgboost import XGBRegressor


# COMMAND ----------

try:
    dbutils.widgets.text("catalog", "apex_fresh")
    catalog = dbutils.widgets.get("catalog").strip() or "apex_fresh"
except NameError:
    # Supports spark_python_task execution where dbutils widgets are unavailable.
    catalog = "apex_fresh"

spark.sql(f"USE CATALOG {catalog}")


# COMMAND ----------

def load_market_df(market: str) -> pd.DataFrame:
    if market == "NEM":
        sdf = spark.sql(
            f"""
            SELECT interval_datetime AS ts, CAST(rrp AS DOUBLE) AS price
            FROM {catalog}.market_nem.prices
            ORDER BY interval_datetime
            """
        )
    elif market == "EPEX":
        sdf = spark.sql(
            f"""
            SELECT delivery_datetime AS ts, CAST(price_eur_mwh AS DOUBLE) AS price
            FROM {catalog}.market_epex.prices
            ORDER BY delivery_datetime
            """
        )
    else:
        sdf = spark.sql(
            f"""
            SELECT interval_datetime AS ts, CAST(lmp AS DOUBLE) AS price
            FROM {catalog}.market_ercot.lmp
            ORDER BY interval_datetime
            """
        )
    pdf = sdf.toPandas()
    pdf["ts"] = pd.to_datetime(pdf["ts"], utc=True)
    return pdf.dropna().reset_index(drop=True)


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["lag_1"] = out["price"].shift(1)
    out["lag_2"] = out["price"].shift(2)
    out["lag_6"] = out["price"].shift(6)
    out["roll_mean_6"] = out["price"].rolling(6).mean().shift(1)
    out["roll_std_6"] = out["price"].rolling(6).std().shift(1).fillna(0.0)
    out["hour"] = out["ts"].dt.hour
    out["dow"] = out["ts"].dt.dayofweek
    return out.dropna().reset_index(drop=True)


def run_market_training(market: str) -> tuple[dict[str, object], dict[str, object], list[dict[str, object]], dict[str, object]]:
    df = build_features(load_market_df(market))
    if len(df) < 60:
        raise ValueError(f"Not enough rows for {market}; need at least 60, got {len(df)}")

    split_idx = int(len(df) * 0.8)
    train = df.iloc[:split_idx]
    test = df.iloc[split_idx:]
    features = ["lag_1", "lag_2", "lag_6", "roll_mean_6", "roll_std_6", "hour", "dow"]

    model = XGBRegressor(
        n_estimators=300,
        max_depth=5,
        learning_rate=0.05,
        subsample=0.9,
        colsample_bytree=0.9,
        objective="reg:squarederror",
        random_state=42,
    )
    model.fit(train[features], train["price"])
    preds = model.predict(test[features])

    mape = float(mean_absolute_percentage_error(test["price"], preds) * 100)
    rmse = float(math.sqrt(mean_squared_error(test["price"], preds)))
    r2 = float(r2_score(test["price"], preds))

    # Simple directional backtest over holdout: +1 if forecast up, -1 if down.
    prev = test["lag_1"].to_numpy()
    direction = np.where(preds >= prev, 1.0, -1.0)
    realized = test["price"].to_numpy() - prev
    pnl_series = direction * realized
    trades = int(len(pnl_series))
    win_rate = float((pnl_series > 0).mean()) if trades else 0.0
    total_pnl = float(pnl_series.sum()) if trades else 0.0
    sharpe = float(pnl_series.mean() / (pnl_series.std() + 1e-9)) if trades else 0.0

    now = datetime.now(timezone.utc)
    with mlflow.start_run(run_name=f"{market.lower()}_price_forecast_train"):
        mlflow.log_params({"market": market, "rows_train": len(train), "rows_test": len(test)})
        mlflow.log_metrics({"mape": mape, "rmse": rmse, "r2": r2, "backtest_total_pnl": total_pnl, "backtest_sharpe": sharpe})
        mlflow.sklearn.log_model(model, artifact_path="model")

    metric_row = {
        "model_name": f"price-forecast-{market.lower()}@champion",
        "market": market,
        "mape": mape,
        "rmse": rmse,
        "r2": r2,
        "run_timestamp": now,
    }
    backtest_row = {
        "strategy": f"{market} Directional Forecast",
        "market": market,
        "trades": trades,
        "win_rate": win_rate,
        "total_pnl": total_pnl,
        "sharpe": sharpe,
        "run_timestamp": now,
    }
    # Generate next 24 horizons using recursive one-step prediction.
    history = df[["ts", "price"]].copy().tail(64).reset_index(drop=True)
    step_minutes = 5 if market in {"NEM", "ERCOT"} else 15
    forecast_rows: list[dict[str, object]] = []
    for _ in range(24):
        last_ts = history["ts"].iloc[-1]
        next_ts = last_ts + pd.Timedelta(minutes=step_minutes)
        lag_1 = float(history["price"].iloc[-1])
        lag_2 = float(history["price"].iloc[-2])
        lag_6 = float(history["price"].iloc[-6])
        roll_mean_6 = float(history["price"].tail(6).mean())
        roll_std_6 = float(history["price"].tail(6).std())
        feat = pd.DataFrame(
            [
                {
                    "lag_1": lag_1,
                    "lag_2": lag_2,
                    "lag_6": lag_6,
                    "roll_mean_6": roll_mean_6,
                    "roll_std_6": 0.0 if np.isnan(roll_std_6) else roll_std_6,
                    "hour": int(next_ts.hour),
                    "dow": int(next_ts.dayofweek),
                }
            ]
        )
        pred = float(model.predict(feat)[0])
        history = pd.concat([history, pd.DataFrame([{"ts": next_ts, "price": pred}])], ignore_index=True)
        forecast_rows.append(
            {
                "market": market,
                "instrument": "MARKET",
                "forecast_datetime": next_ts,
                "forecast_price": pred,
                "forecast_demand_mw": 0.0,
                "model_name": f"price-forecast-{market.lower()}@champion",
                "run_timestamp": now,
            }
        )

    feature_set = ",".join(features)
    lineage_row = {
        "market": market,
        "model_name": f"price-forecast-{market.lower()}@champion",
        "run_timestamp": now,
        "training_start_utc": train["ts"].min(),
        "training_end_utc": train["ts"].max(),
        "feature_set": feature_set,
        "feature_hash": hashlib.sha256(feature_set.encode("utf-8")).hexdigest(),
    }

    return metric_row, backtest_row, forecast_rows, lineage_row


# COMMAND ----------

metrics: list[dict[str, object]] = []
backtests: list[dict[str, object]] = []
forecasts: list[dict[str, object]] = []
lineage: list[dict[str, object]] = []
for m in ["NEM", "EPEX", "ERCOT"]:
    metric_row, backtest_row, forecast_rows, lineage_row = run_market_training(m)
    metrics.append(metric_row)
    backtests.append(backtest_row)
    forecasts.extend(forecast_rows)
    lineage.append(lineage_row)

spark.createDataFrame(pd.DataFrame(metrics)).write.mode("append").saveAsTable(f"{catalog}.analytics.model_performance")
spark.createDataFrame(pd.DataFrame(backtests)).write.mode("append").saveAsTable(f"{catalog}.analytics.backtest_runs")
spark.createDataFrame(pd.DataFrame(forecasts)).write.mode("append").saveAsTable(f"{catalog}.analytics.price_forecasts")
spark.createDataFrame(pd.DataFrame(lineage)).write.mode("append").saveAsTable(f"{catalog}.analytics.model_lineage")

display(spark.sql(f"SELECT * FROM {catalog}.analytics.model_performance ORDER BY run_timestamp DESC LIMIT 9"))
display(spark.sql(f"SELECT * FROM {catalog}.analytics.backtest_runs ORDER BY run_timestamp DESC LIMIT 9"))
display(spark.sql(f"SELECT * FROM {catalog}.analytics.price_forecasts ORDER BY run_timestamp DESC, forecast_datetime ASC LIMIT 30"))
display(spark.sql(f"SELECT * FROM {catalog}.analytics.model_lineage ORDER BY run_timestamp DESC LIMIT 9"))
