from __future__ import annotations

from decimal import Decimal

from fastapi import APIRouter, Query
from pydantic import BaseModel

from apex_fresh.app.backend.models import APIResponse
from apex_fresh.app.backend.store import STORE

router = APIRouter(prefix="/api/v1/positions", tags=["positions"])


class PositionRow(BaseModel):
    instrument_id: str
    market: str
    trader_id: str
    net_volume_mw: Decimal
    avg_price: Decimal
    market_price: Decimal
    mtm_pnl: Decimal


class SourceLag(BaseModel):
    market: str
    source_system: str
    lag_seconds: int
    status: str


@router.get("/", response_model=APIResponse[list[PositionRow]])
def book(market: str | None = Query(default=None, pattern="^(NEM|EPEX|ERCOT)$")) -> APIResponse[list[PositionRow]]:
    rows: list[PositionRow] = []
    for trade in STORE.trades:
        if market and trade.market != market:
            continue
        if trade.market == "NEM":
            mkt = Decimal("95")
        elif trade.market == "EPEX":
            mkt = Decimal("70")
        else:
            mkt = Decimal("48")
        sign = Decimal("1") if trade.direction == "BUY" else Decimal("-1")
        net = sign * trade.volume_mw
        mtm = (mkt - trade.price) * net
        rows.append(
            PositionRow(
                instrument_id=trade.instrument_id,
                market=trade.market,
                trader_id=trade.trader_id,
                net_volume_mw=net,
                avg_price=trade.price,
                market_price=mkt,
                mtm_pnl=mtm,
            )
        )
    return APIResponse(data=rows)


@router.get("/source-lag", response_model=APIResponse[list[SourceLag]])
def source_lag() -> APIResponse[list[SourceLag]]:
    rows = [
        SourceLag(market="NEM", source_system="ALIGNE_SIM", lag_seconds=21, status="FRESH"),
        SourceLag(market="EPEX", source_system="ENDUR_SIM", lag_seconds=43, status="FRESH"),
        SourceLag(market="ERCOT", source_system="TRIPLE_POINT_SIM", lag_seconds=38, status="FRESH"),
    ]
    return APIResponse(data=rows)

