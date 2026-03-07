from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from app.backend.config import get_settings
from app.backend.database import execute_sql
from app.backend.models import APIResponse

router = APIRouter(prefix="/api/v1/positions", tags=["positions"])


class PositionRow(BaseModel):
    instrument: str
    net_position_mw: float
    avg_trade_price: float


@router.get("/book", response_model=APIResponse[list[PositionRow]])
async def position_book() -> APIResponse[list[PositionRow]]:
    catalog = get_settings().apex_catalog
    sql = (
        f"SELECT instrument_id AS instrument, "
        f"SUM(CASE WHEN upper(direction)='BUY' THEN volume_mw ELSE -volume_mw END) AS net_position_mw, "
        f"CASE WHEN SUM(volume_mw)=0 THEN 0 ELSE SUM(price*volume_mw)/SUM(volume_mw) END AS avg_trade_price "
        f"FROM {catalog}.trading.trades GROUP BY instrument_id ORDER BY instrument_id"
    )
    rows = [PositionRow.model_validate(r) for r in await execute_sql(sql)]
    return APIResponse(data=rows, region="GLOBAL")
