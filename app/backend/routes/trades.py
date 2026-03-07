from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.backend.config import get_settings
from app.backend.database import execute_sql
from app.backend.models import APIResponse
from app.backend.sql_loader import load_sql

router = APIRouter(prefix="/api/v1/trades", tags=["trades"])


class TradeEntryRequest(BaseModel):
    trader: str = Field(min_length=2)
    instrument: str
    side: str
    volume_mw: float = Field(gt=0)
    price: float = Field(gt=0)
    counterparty: str | None = None


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


class DailyPnL(BaseModel):
    market: str
    pnl_daily: float


class ExposureHeatmapRow(BaseModel):
    instrument: str
    q1: float
    q2: float
    q3: float
    q4: float


class CounterpartyRow(BaseModel):
    counterparty: str


def _escape(value: str) -> str:
    return value.replace("'", "''")

def _instrument_market(instrument: str) -> str:
    value = instrument.upper()
    if value.startswith(('NSW_', 'VIC_', 'QLD_', 'SA_', 'FCAS_')):
        return 'NEM'
    if value.startswith(('DE-LU_', 'FR_', 'BE_', 'NL_', 'ES_')):
        return 'EPEX'
    if value.startswith('ERCOT_'):
        return 'ERCOT'
    return 'NEM'


@router.post("/entry", response_model=APIResponse[TradeEntryResponse])
async def create_trade(payload: TradeEntryRequest) -> APIResponse[TradeEntryResponse]:
    trade_id = f"TRD-{uuid4().hex[:8].upper()}"
    now = datetime.now(timezone.utc)
    catalog = get_settings().apex_catalog
    market = _instrument_market(payload.instrument)
    statement = (
        f"INSERT INTO {catalog}.trading.trades "
        f"(trade_id, market, instrument_id, trader_id, direction, volume_mw, price, source_system, ingested_at) VALUES ("
        f"'{trade_id}', '{market}', "
        f"'{_escape(payload.instrument)}', '{_escape(payload.trader)}', "
        f"'{_escape(payload.side.upper())}', {payload.volume_mw}, {payload.price}, "
        f"'APEX_UI', TIMESTAMP '{now.strftime('%Y-%m-%d %H:%M:%S')}'"
        f")"
    )
    try:
        await execute_sql(statement)
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Trade insert failed: {exc}") from exc
    return APIResponse(
        data=TradeEntryResponse(
            trade_id=trade_id,
            status="ACCEPTED",
            created_at=now,
        ),
        region="GLOBAL",
    )


@router.get("/blotter", response_model=APIResponse[list[TradeRow]])
async def blotter(market: str | None = Query(default=None)) -> APIResponse[list[TradeRow]]:
    sql = load_sql('data/queries/trades/trade_blotter.sql')
    if market:
        sql = sql.replace("-- __MARKET_FILTER__", f"WHERE upper(t.market)='{market.upper()}'")
    else:
        sql = sql.replace("-- __MARKET_FILTER__", "")
    rows = await execute_sql(sql)
    out = [
        TradeRow(
            trade_id=str(r.get('trade_id')),
            trader=str(r.get('trader_id')),
            instrument=str(r.get('instrument_id')),
            side=str(r.get('direction')),
            volume_mw=float(r.get('volume_mw', 0)),
            price=float(r.get('price', 0)),
            counterparty=str(r.get('source_system', 'UNKNOWN')),
            trade_time=r.get('ingested_at') or datetime.now(timezone.utc),
            mtm_pnl=float(r.get('mtm_pnl', 0)),
        )
        for r in rows
    ]
    return APIResponse(data=out, region="GLOBAL")


@router.get("/pnl-daily", response_model=APIResponse[DailyPnL])
async def pnl_daily(market: str = Query(default='NEM')) -> APIResponse[DailyPnL]:
    market_key = market.upper()
    catalog = get_settings().apex_catalog
    sql = (
        f"SELECT COALESCE(SUM(CASE WHEN upper(direction)='BUY' THEN -price*volume_mw ELSE price*volume_mw END),0) AS pnl_daily "
        f"FROM {catalog}.trading.trades WHERE upper(market)='{market_key}'"
    )
    rows = await execute_sql(sql)
    pnl = float(rows[0].get('pnl_daily', 0)) if rows else 0.0
    return APIResponse(data=DailyPnL(market=market_key, pnl_daily=round(pnl, 2)), region=market_key)


@router.get("/exposure-heatmap", response_model=APIResponse[list[ExposureHeatmapRow]])
async def exposure_heatmap(market: str = Query(default='NEM')) -> APIResponse[list[ExposureHeatmapRow]]:
    catalog = get_settings().apex_catalog
    market_key = market.upper()
    sql = (
        f"WITH base AS ("
        f"  SELECT instrument_id AS instrument, "
        f"         CASE WHEN hour(ingested_at) BETWEEN 0 AND 5 THEN 'Q1' "
        f"              WHEN hour(ingested_at) BETWEEN 6 AND 11 THEN 'Q2' "
        f"              WHEN hour(ingested_at) BETWEEN 12 AND 17 THEN 'Q3' "
        f"              ELSE 'Q4' END AS q, "
        f"         CASE WHEN upper(direction)='BUY' THEN volume_mw ELSE -volume_mw END AS signed_mw "
        f"  FROM {catalog}.trading.trades "
        f"  WHERE upper(market)='{market_key}'"
        f") "
        f"SELECT instrument, "
        f"  COALESCE(SUM(CASE WHEN q='Q1' THEN signed_mw END),0) AS q1, "
        f"  COALESCE(SUM(CASE WHEN q='Q2' THEN signed_mw END),0) AS q2, "
        f"  COALESCE(SUM(CASE WHEN q='Q3' THEN signed_mw END),0) AS q3, "
        f"  COALESCE(SUM(CASE WHEN q='Q4' THEN signed_mw END),0) AS q4 "
        f"FROM base GROUP BY instrument ORDER BY instrument"
    )
    rows = await execute_sql(sql)
    out = [ExposureHeatmapRow.model_validate(r) for r in rows]
    return APIResponse(data=out, region=market_key)


@router.get("/counterparties", response_model=APIResponse[list[CounterpartyRow]])
async def counterparties(market: str = Query(default='NEM')) -> APIResponse[list[CounterpartyRow]]:
    catalog = get_settings().apex_catalog
    market_key = market.upper()
    rows = await execute_sql(
        f"SELECT DISTINCT COALESCE(source_system, 'UNKNOWN') AS counterparty "
        f"FROM {catalog}.trading.trades "
        f"WHERE upper(market)='{market_key}' "
        f"ORDER BY counterparty"
    )
    out = [CounterpartyRow.model_validate(r) for r in rows]
    return APIResponse(data=out, region=market_key)
