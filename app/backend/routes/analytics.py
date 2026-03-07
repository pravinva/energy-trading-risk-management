from __future__ import annotations

from datetime import datetime, timezone
from fastapi import APIRouter
from pydantic import BaseModel

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


@router.get("/model-performance", response_model=APIResponse[list[ModelMetric]])
async def model_performance() -> APIResponse[list[ModelMetric]]:
    now = datetime.now(timezone.utc)
    rows = [
        ModelMetric(model_name="price-forecast-xgb@champion", mape=6.4, rmse=8.1, r2=0.88, run_timestamp=now),
        ModelMetric(model_name="dispatch-policy-xgb@challenger", mape=7.1, rmse=8.8, r2=0.84, run_timestamp=now),
    ]
    return APIResponse(data=rows, region="GLOBAL")


@router.get("/backtests", response_model=APIResponse[list[BacktestSummary]])
async def backtests() -> APIResponse[list[BacktestSummary]]:
    rows = [
        BacktestSummary(strategy="Spike Capture", trades=412, win_rate=0.62, total_pnl=2_430_500.55, sharpe=1.48),
        BacktestSummary(strategy="Battery Spread Arbitrage", trades=358, win_rate=0.59, total_pnl=1_932_445.31, sharpe=1.31),
    ]
    return APIResponse(data=rows, region="GLOBAL")
