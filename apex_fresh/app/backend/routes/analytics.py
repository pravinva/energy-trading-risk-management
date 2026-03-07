from __future__ import annotations

from fastapi import APIRouter, Query
from pydantic import BaseModel

from apex_fresh.app.backend.models import APIResponse

router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])


class ModelPerformance(BaseModel):
    market: str
    region_id: str
    mape: float
    rmse: float
    bias: float


@router.get("/model-performance", response_model=APIResponse[list[ModelPerformance]])
def model_performance(
    market: str = Query(pattern="^(NEM|EPEX|ERCOT)$"),
    region_id: str = "NSW1",
) -> APIResponse[list[ModelPerformance]]:
    return APIResponse(
        data=[
            ModelPerformance(market=market, region_id=region_id, mape=6.2, rmse=8.1, bias=-0.3),
            ModelPerformance(market=market, region_id=region_id, mape=7.0, rmse=9.2, bias=0.2),
        ]
    )


@router.post("/backtest/run", response_model=APIResponse[dict[str, str]])
def run_backtest() -> APIResponse[dict[str, str]]:
    return APIResponse(data={"run_id": "BT-001", "status": "COMPLETED"})

