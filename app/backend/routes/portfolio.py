from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from app.backend.models import APIResponse

router = APIRouter(prefix="/api/v1/portfolio", tags=["portfolio"])


class RevenueComponent(BaseModel):
    component: str
    annual_value: float
    contribution_pct: float


class PPARow(BaseModel):
    ppa_id: str
    counterparty: str
    volume_mw: float
    strike_price: float
    tenor_years: int


@router.get("/revenue-stacking", response_model=APIResponse[list[RevenueComponent]])
async def revenue_stacking() -> APIResponse[list[RevenueComponent]]:
    rows = [
        RevenueComponent(component="Energy Arbitrage", annual_value=18_500_000, contribution_pct=38.4),
        RevenueComponent(component="FCAS", annual_value=14_200_000, contribution_pct=29.5),
        RevenueComponent(component="Capacity", annual_value=7_500_000, contribution_pct=15.6),
        RevenueComponent(component="PPA Hedge Value", annual_value=8_000_000, contribution_pct=16.5),
    ]
    return APIResponse(data=rows, region="GLOBAL")


@router.get("/ppa-book", response_model=APIResponse[list[PPARow]])
async def ppa_book() -> APIResponse[list[PPARow]]:
    rows = [
        PPARow(ppa_id="PPA-001", counterparty="IndustrialCo", volume_mw=65.0, strike_price=84.0, tenor_years=7),
        PPARow(ppa_id="PPA-002", counterparty="CloudWorks", volume_mw=42.0, strike_price=91.5, tenor_years=10),
        PPARow(ppa_id="PPA-003", counterparty="TransitGrid", volume_mw=28.0, strike_price=88.0, tenor_years=5),
    ]
    return APIResponse(data=rows, region="GLOBAL")
