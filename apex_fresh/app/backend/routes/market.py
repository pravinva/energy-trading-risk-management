from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, Query
from pydantic import BaseModel

from apex_fresh.app.backend.models import APIResponse
from apex_fresh.app.backend.store import STORE

router = APIRouter(prefix="/api/v1/market", tags=["market"])


class NEMPrice(BaseModel):
    region_id: str
    rrp: Decimal
    change_vs_prev: Decimal
    interval_datetime: datetime
    currency: str = "AUD"


class EPEXPrice(BaseModel):
    bidding_zone: str
    price_eur_mwh: Decimal
    mtu_minutes: int
    delivery_datetime: datetime
    currency: str = "EUR"


class ERCOTPrice(BaseModel):
    node_id: str
    lmp: Decimal
    rtcb_signal: Decimal | None
    interval_datetime: datetime
    currency: str = "USD"


class MarketSummary(BaseModel):
    market_id: str
    avg_price: Decimal
    change_24h: Decimal
    currency: str


@router.get("/nem/prices/current", response_model=APIResponse[list[NEMPrice]])
def nem_prices_current() -> APIResponse[list[NEMPrice]]:
    rows = [
        NEMPrice(
            region_id=point.key,
            rrp=point.value,
            change_vs_prev=point.value - point.previous,
            interval_datetime=point.ts,
        )
        for point in STORE.nem_prices.values()
    ]
    return APIResponse(data=rows)


@router.get("/epex/prices/current", response_model=APIResponse[list[EPEXPrice]])
def epex_prices_current() -> APIResponse[list[EPEXPrice]]:
    rows = [
        EPEXPrice(
            bidding_zone=point.key,
            price_eur_mwh=point.value,
            mtu_minutes=15,
            delivery_datetime=point.ts,
        )
        for point in STORE.epex_prices.values()
    ]
    return APIResponse(data=rows)


@router.get("/ercot/lmp/current", response_model=APIResponse[list[ERCOTPrice]])
def ercot_lmp_current() -> APIResponse[list[ERCOTPrice]]:
    rows = [
        ERCOTPrice(
            node_id=point.key,
            lmp=point.value,
            rtcb_signal=point.value + Decimal("0.7"),
            interval_datetime=point.ts,
        )
        for point in STORE.ercot_lmp.values()
    ]
    return APIResponse(data=rows)


@router.get("/summary", response_model=APIResponse[list[MarketSummary]])
def summary() -> APIResponse[list[MarketSummary]]:
    def _avg(values: list[Decimal]) -> Decimal:
        return sum(values) / Decimal(len(values)) if values else Decimal("0")

    out = [
        MarketSummary(
            market_id="NEM",
            avg_price=_avg([p.value for p in STORE.nem_prices.values()]),
            change_24h=Decimal("2.1"),
            currency="AUD",
        ),
        MarketSummary(
            market_id="EPEX",
            avg_price=_avg([p.value for p in STORE.epex_prices.values()]),
            change_24h=Decimal("-1.4"),
            currency="EUR",
        ),
        MarketSummary(
            market_id="ERCOT",
            avg_price=_avg([p.value for p in STORE.ercot_lmp.values()]),
            change_24h=Decimal("3.7"),
            currency="USD",
        ),
    ]
    return APIResponse(data=out)


@router.get("/prices/history", response_model=APIResponse[list[dict[str, str]]])
def generic_history(
    market: str = Query(pattern="^(NEM|EPEX|ERCOT)$"),
    hours: int = Query(default=24, ge=1, le=168),
) -> APIResponse[list[dict[str, str]]]:
    return APIResponse(data=[{"market": market, "hours": str(hours), "status": "ok"}])

