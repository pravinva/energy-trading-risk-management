from __future__ import annotations

from decimal import Decimal

from fastapi import APIRouter, Query
from pydantic import BaseModel

from apex_fresh.app.backend.models import APIResponse

router = APIRouter(prefix="/api/v1/portfolio", tags=["portfolio"])


class RevenueActual(BaseModel):
    asset_id: str
    market: str
    total_revenue: Decimal
    currency: str


@router.get("/revenue/actuals", response_model=APIResponse[list[RevenueActual]])
def revenue_actuals(
    market: str = Query(pattern="^(NEM|EPEX|ERCOT)$"),
) -> APIResponse[list[RevenueActual]]:
    currency = {"NEM": "AUD", "EPEX": "EUR", "ERCOT": "USD"}[market]
    rows = [
        RevenueActual(asset_id=f"{market}_BESS_1", market=market, total_revenue=Decimal("1520000.45"), currency=currency),
        RevenueActual(asset_id=f"{market}_BESS_2", market=market, total_revenue=Decimal("1320044.02"), currency=currency),
    ]
    return APIResponse(data=rows)


@router.get("/ppa", response_model=APIResponse[list[dict[str, str]]])
def ppa_book(market: str = Query(pattern="^(NEM|EPEX|ERCOT)$")) -> APIResponse[list[dict[str, str]]]:
    return APIResponse(data=[{"market": market, "ppa_id": "PPA-001", "status": "ACTIVE"}])

