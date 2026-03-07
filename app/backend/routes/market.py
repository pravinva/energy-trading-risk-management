from __future__ import annotations

from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Query
from pydantic import BaseModel

from app.backend.data_store import americas_current, anz_prices_current, europe_prices_current
from app.backend.models import APIResponse

router = APIRouter(prefix="/api/v1/market", tags=["market"])


class CurrentPrice(BaseModel):
    market: str
    instrument: str
    price: float
    change_pct: float
    timestamp: datetime


class PredispatchPoint(BaseModel):
    interval_start: datetime
    region: str
    forecast_price: float
    forecast_demand_mw: float


class ForwardCurvePoint(BaseModel):
    tenor: str
    hub: str
    price: float


class MarketSummary(BaseModel):
    active_markets: int
    instruments_tracked: int
    average_price: float
    last_refresh_utc: datetime


@router.get("/current-prices", response_model=APIResponse[list[CurrentPrice]])
async def current_prices() -> APIResponse[list[CurrentPrice]]:
    now = datetime.now(timezone.utc)
    rows: list[CurrentPrice] = []
    for r in anz_prices_current():
        rows.append(CurrentPrice(market="ANZ", instrument=str(r["region_id"]), price=float(r["rrp"]), change_pct=float(r["pct_change"]), timestamp=now))
    for r in europe_prices_current()[:6]:
        rows.append(CurrentPrice(market="EU", instrument=str(r["bidding_zone"]), price=float(r["price_eur_mwh"]), change_pct=0.0, timestamp=now))
    for r in americas_current()[:6]:
        rows.append(CurrentPrice(market="US", instrument=str(r["node_id"]), price=float(r["lmp"]), change_pct=0.0, timestamp=now))
    return APIResponse(data=rows, region="GLOBAL")


@router.get("/predispatch", response_model=APIResponse[list[PredispatchPoint]])
async def predispatch(hours: int = Query(default=24, ge=1, le=168)) -> APIResponse[list[PredispatchPoint]]:
    now = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
    points = [
        PredispatchPoint(
            interval_start=now + timedelta(hours=i),
            region=region,
            forecast_price=round(85 + (i * 0.7) + (4 if region == "SA" else 0), 2),
            forecast_demand_mw=round(6800 + i * 15 + (130 if region == "NSW" else 0), 2),
        )
        for i in range(hours)
        for region in ["QLD", "NSW", "VIC", "SA"]
    ]
    return APIResponse(data=points, region="ANZ")


@router.get("/forward-curves", response_model=APIResponse[list[ForwardCurvePoint]])
async def forward_curves() -> APIResponse[list[ForwardCurvePoint]]:
    tenors = ["M+1", "M+2", "Q+1", "Q+2", "CAL+1"]
    hubs = ["NSW", "VIC", "SA", "ERCOT_HOUSTON", "DE-LU"]
    out = [
        ForwardCurvePoint(tenor=t, hub=h, price=round(70 + i * 3 + j * 1.5, 2))
        for i, t in enumerate(tenors)
        for j, h in enumerate(hubs)
    ]
    return APIResponse(data=out, region="GLOBAL")


@router.get("/summary", response_model=APIResponse[MarketSummary])
async def summary() -> APIResponse[MarketSummary]:
    prices = [float(r["rrp"]) for r in anz_prices_current()]
    prices += [float(r["price_eur_mwh"]) for r in europe_prices_current()]
    prices += [float(r["lmp"]) for r in americas_current()]
    avg = sum(prices) / len(prices) if prices else 0.0
    return APIResponse(
        data=MarketSummary(
            active_markets=3,
            instruments_tracked=len(prices),
            average_price=round(avg, 2),
            last_refresh_utc=datetime.now(timezone.utc),
        ),
        region="GLOBAL",
    )
