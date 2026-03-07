from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.backend.apex_store import STORE, TradeRecord
from app.backend.engines.pnl import mark_to_market
from app.backend.models import APIResponse

router = APIRouter(prefix="/api/v1/trades", tags=["trades"])


class TradeEntryRequest(BaseModel):
    trader: str = Field(min_length=2)
    instrument: str
    side: str
    volume_mw: float = Field(gt=0)
    price: float = Field(gt=0)
    counterparty: str


class TradeEntryResponse(BaseModel):
    trade_id: str
    status: str
    created_at: datetime


class TradeRow(BaseModel):
    trade_id: str
    trader: str
    instrument: str
    side: str
    volume_mw: float
    price: float
    counterparty: str
    trade_time: datetime
    mtm_pnl: float


@router.post("/entry", response_model=APIResponse[TradeEntryResponse])
async def create_trade(payload: TradeEntryRequest) -> APIResponse[TradeEntryResponse]:
    trade = TradeRecord(
        trade_id=f"TRD-{uuid4().hex[:8].upper()}",
        trader=payload.trader,
        instrument=payload.instrument,
        side=payload.side.upper(),
        volume_mw=payload.volume_mw,
        price=payload.price,
        counterparty=payload.counterparty,
        trade_time=datetime.now(timezone.utc),
    )
    STORE.add_trade(trade)
    return APIResponse(
        data=TradeEntryResponse(
            trade_id=trade.trade_id,
            status="ACCEPTED",
            created_at=trade.trade_time,
        ),
        region="GLOBAL",
    )


@router.get("/blotter", response_model=APIResponse[list[TradeRow]])
async def blotter() -> APIResponse[list[TradeRow]]:
    market_marks = {
        "NSW_BASE": 102.0,
        "VIC_PEAK": 121.5,
        "FCAS_RAISE6SEC": 14.8,
        "ERCOT_HOUSTON": 85.4,
        "DE-LU_BASE": 76.1,
    }
    rows = []
    for t in STORE.list_trades():
        mark = market_marks.get(t.instrument, t.price)
        pnl = mark_to_market(t.side, t.volume_mw, t.price, mark)
        rows.append(
            TradeRow(
                trade_id=t.trade_id,
                trader=t.trader,
                instrument=t.instrument,
                side=t.side,
                volume_mw=t.volume_mw,
                price=t.price,
                counterparty=t.counterparty,
                trade_time=t.trade_time,
                mtm_pnl=pnl,
            )
        )
    rows.sort(key=lambda r: r.trade_time, reverse=True)
    return APIResponse(data=rows, region="GLOBAL")
