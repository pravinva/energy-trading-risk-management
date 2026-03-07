from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from app.backend.apex_store import STORE
from app.backend.engines.position import build_position_book
from app.backend.models import APIResponse

router = APIRouter(prefix="/api/v1/positions", tags=["positions"])


class PositionRow(BaseModel):
    instrument: str
    net_position_mw: float
    avg_trade_price: float


@router.get("/book", response_model=APIResponse[list[PositionRow]])
async def position_book() -> APIResponse[list[PositionRow]]:
    trades = [
        {
            "instrument": t.instrument,
            "side": t.side,
            "volume_mw": t.volume_mw,
            "price": t.price,
        }
        for t in STORE.list_trades()
    ]
    rows = [PositionRow.model_validate(r) for r in build_position_book(trades)]
    return APIResponse(data=rows, region="GLOBAL")
