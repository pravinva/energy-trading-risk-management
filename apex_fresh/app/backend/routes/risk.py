from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
import random

from fastapi import APIRouter
from pydantic import BaseModel, Field

from apex_fresh.app.backend.models import APIResponse

router = APIRouter(prefix="/api/v1/risk", tags=["risk"])


class VaRRequest(BaseModel):
    market: str = Field(pattern="^(NEM|EPEX|ERCOT)$")
    simulation_count: int = Field(default=10_000, ge=1_000, le=100_000)


class VaRResult(BaseModel):
    market: str
    var_95: Decimal
    var_99: Decimal
    cvar_95: Decimal
    cvar_99: Decimal
    simulation_count: int
    calculated_at: datetime


@router.post("/var/calculate", response_model=APIResponse[VaRResult])
def calculate_var(request: VaRRequest) -> APIResponse[VaRResult]:
    base = Decimal(str(random.uniform(1_000_000, 2_000_000)))
    var_95 = base.quantize(Decimal("0.01"))
    var_99 = (base * Decimal("1.45")).quantize(Decimal("0.01"))
    cvar_95 = (var_95 * Decimal("1.10")).quantize(Decimal("0.01"))
    cvar_99 = (var_99 * Decimal("1.08")).quantize(Decimal("0.01"))
    return APIResponse(
        data=VaRResult(
            market=request.market,
            var_95=var_95,
            var_99=var_99,
            cvar_95=cvar_95,
            cvar_99=cvar_99,
            simulation_count=request.simulation_count,
            calculated_at=datetime.now(timezone.utc),
        )
    )


@router.get("/limits/breaches", response_model=APIResponse[list[dict[str, str]]])
def breaches() -> APIResponse[list[dict[str, str]]]:
    return APIResponse(data=[{"trader": "SCHEN", "limit_type": "VAR", "status": "ACTIVE"}])

