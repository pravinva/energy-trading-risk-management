from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter
from pydantic import BaseModel

from app.backend.config import get_settings
from app.backend.database import execute_sql
from app.backend.models import APIResponse

router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])


class ModelMetric(BaseModel):
    model_name: str
    mape: float
    rmse: float
    r2: float
    run_timestamp: datetime


class BacktestSummary(BaseModel):
    strategy: str
    trades: int
    win_rate: float
    total_pnl: float
    sharpe: float


class ModelLineage(BaseModel):
    market: str
    model_name: str
    run_timestamp: datetime
    training_start_utc: datetime
    training_end_utc: datetime
    feature_set: str
    feature_hash: str


class StrategyAvailability(BaseModel):
    market: str
    strategy: str
    available: bool


@router.get("/model-performance", response_model=APIResponse[list[ModelMetric]])
async def model_performance() -> APIResponse[list[ModelMetric]]:
    catalog = get_settings().apex_catalog
    sql = (
        f"SELECT model_name, mape, rmse, r2, run_timestamp "
        f"FROM {catalog}.analytics.model_performance "
        f"ORDER BY run_timestamp DESC LIMIT 100"
    )
    rows = await execute_sql(sql)
    out = [ModelMetric.model_validate(r) for r in rows]
    return APIResponse(data=out, region="GLOBAL")


@router.get("/backtests", response_model=APIResponse[list[BacktestSummary]])
async def backtests() -> APIResponse[list[BacktestSummary]]:
    catalog = get_settings().apex_catalog
    sql = (
        f"SELECT strategy, trades, win_rate, total_pnl, sharpe "
        f"FROM {catalog}.analytics.backtest_runs "
        f"ORDER BY run_timestamp DESC LIMIT 100"
    )
    rows = await execute_sql(sql)
    out = [BacktestSummary.model_validate(r) for r in rows]
    return APIResponse(data=out, region="GLOBAL")


@router.get("/model-lineage", response_model=APIResponse[list[ModelLineage]])
async def model_lineage(market: str | None = None) -> APIResponse[list[ModelLineage]]:
    catalog = get_settings().apex_catalog
    await execute_sql(
        f"""
        CREATE TABLE IF NOT EXISTS {catalog}.analytics.model_lineage (
          market STRING,
          model_name STRING,
          run_timestamp TIMESTAMP,
          training_start_utc TIMESTAMP,
          training_end_utc TIMESTAMP,
          feature_set STRING,
          feature_hash STRING
        )
        """
    )
    market_filter = ""
    if market:
        safe_market = market.replace("'", "''")
        market_filter = f"WHERE market = '{safe_market}'"
    sql = f"""
        WITH ranked AS (
          SELECT
            market,
            model_name,
            run_timestamp,
            training_start_utc,
            training_end_utc,
            feature_set,
            feature_hash,
            ROW_NUMBER() OVER (PARTITION BY market ORDER BY run_timestamp DESC) AS rn
          FROM {catalog}.analytics.model_lineage
          {market_filter}
        )
        SELECT
          market,
          model_name,
          run_timestamp,
          training_start_utc,
          training_end_utc,
          feature_set,
          feature_hash
        FROM ranked
        WHERE rn = 1
        ORDER BY market
    """
    rows = await execute_sql(sql)
    out = [ModelLineage.model_validate(r) for r in rows]
    return APIResponse(data=out, region=market or "GLOBAL")


@router.get("/strategies", response_model=APIResponse[list[StrategyAvailability]])
async def strategies(market: str) -> APIResponse[list[StrategyAvailability]]:
    catalog = get_settings().apex_catalog
    market_key = market.upper()
    await execute_sql(
        f"CREATE TABLE IF NOT EXISTS {catalog}.analytics.strategy_catalog ("
        f"market STRING, strategy STRING, available BOOLEAN)"
    )
    rows = await execute_sql(
        f"SELECT upper(market) AS market, strategy, available "
        f"FROM {catalog}.analytics.strategy_catalog "
        f"WHERE upper(market)='{market_key}' "
        f"ORDER BY strategy"
    )
    out = [StrategyAvailability.model_validate(r) for r in rows]
    return APIResponse(data=out, region=market_key)
