from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

from fastapi import APIRouter, Query
from pydantic import BaseModel

from apex_fresh.app.backend.models import APIResponse
from apex_fresh.app.backend.store import STORE, Trade

router = APIRouter(prefix="/api/v1/trades", tags=["trades"])


class TradeRow(BaseModel):
    trade_id: str
    market: str
    instrument_id: str
    trader_id: str
    direction: str
    volume_mw: Decimal
    price: Decimal
    source_system: str
    ingested_at: datetime


def _seed_once() -> None:
    if STORE.trades:
        return
    now = datetime.now(timezone.utc)
    for market, source in [("NEM", "ALIGNE_SIM"), ("EPEX", "ENDUR_SIM"), ("ERCOT", "TRIPLE_POINT_SIM")]:
        STORE.trades.append(
            Trade(
                trade_id=f"TRD-{uuid4().hex[:8].upper()}",
                market=market,
                instrument_id=f"{market}_SPOT_MAIN",
                trader_id="SCHEN",
                direction="BUY",
                volume_mw=Decimal("100"),
                price=Decimal("80"),
                source_system=source,
                ingested_at=now,
            )
        )


@router.get("/", response_model=APIResponse[list[TradeRow]])
def trade_blotter(
    market: str | None = Query(default=None, pattern="^(NEM|EPEX|ERCOT)$"),
    days: int = Query(default=30, ge=1, le=365),
) -> APIResponse[list[TradeRow]]:
    _seed_once()
    rows = STORE.trades
    if market:
        rows = [t for t in rows if t.market == market]
    return APIResponse(data=[TradeRow(**t.__dict__) for t in rows[: max(days, 1)]])


@router.get("/{trade_id}", response_model=APIResponse[TradeRow])
def trade_by_id(trade_id: str) -> APIResponse[TradeRow]:
    _seed_once()
    for trade in STORE.trades:
        if trade.trade_id == trade_id:
            return APIResponse(data=TradeRow(**trade.__dict__))
    # deterministic fallback for demo paths
    fallback = STORE.trades[0]
    return APIResponse(data=TradeRow(**fallback.__dict__), message=f"not found, returned fallback for {trade_id}")

