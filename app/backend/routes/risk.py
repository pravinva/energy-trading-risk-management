from __future__ import annotations

from datetime import datetime, timezone
from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.backend.apex_store import STORE
from app.backend.engines.var import calculate_var
from app.backend.models import APIResponse

router = APIRouter(prefix="/api/v1/risk", tags=["risk"])


class VaRRequest(BaseModel):
    confidence: float = Field(default=0.95, ge=0.9, le=0.99)
    volatility: float = Field(default=0.12, gt=0)
    spot_price: float = Field(default=96.0, gt=0)


class VaRResponse(BaseModel):
    exposure_mw: float
    var_95: float
    var_99: float
    expected_shortfall_95: float
    calculated_at: datetime


class LimitStatus(BaseModel):
    metric: str
    current: float
    limit: float
    breached: bool


@router.post("/var/calculate", response_model=APIResponse[VaRResponse])
async def var_calculate(payload: VaRRequest) -> APIResponse[VaRResponse]:
    exposure = sum(
        t.volume_mw if t.side == "BUY" else -t.volume_mw
        for t in STORE.list_trades()
    )
    metrics = calculate_var(
        exposure_mw=exposure,
        spot_price=payload.spot_price,
        volatility=payload.volatility,
    )
    return APIResponse(
        data=VaRResponse(
            exposure_mw=round(exposure, 2),
            var_95=metrics["var_95"],
            var_99=metrics["var_99"],
            expected_shortfall_95=metrics["expected_shortfall_95"],
            calculated_at=datetime.now(timezone.utc),
        ),
        region="GLOBAL",
    )


@router.get("/limits/status", response_model=APIResponse[list[LimitStatus]])
async def limits_status() -> APIResponse[list[LimitStatus]]:
    gross_exposure = sum(abs(t.volume_mw) for t in STORE.list_trades())
    pnl_drawdown = max(0.0, gross_exposure * 1.9)
    rows = [
        LimitStatus(metric="Gross MW", current=round(gross_exposure, 2), limit=5_000.0, breached=gross_exposure > 5_000.0),
        LimitStatus(metric="Intraday Drawdown", current=round(pnl_drawdown, 2), limit=50_000.0, breached=pnl_drawdown > 50_000.0),
    ]
    return APIResponse(data=rows, region="GLOBAL")
