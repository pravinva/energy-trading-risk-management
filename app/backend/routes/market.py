from __future__ import annotations

from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.backend.config import get_settings
from app.backend.database import execute_sql
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


class InstrumentQuote(BaseModel):
    market: str
    instrument: str
    last_price: float
    change_pct: float
    bid: float
    offer: float
    volume: float
    status: str


class ForecastMetadata(BaseModel):
    market: str
    model_name: str
    last_run_utc: datetime | None
    points_available: int
    first_forecast_utc: datetime | None
    last_forecast_utc: datetime | None


class MarketInstrument(BaseModel):
    market: str
    instrument: str


class SpotPrice(BaseModel):
    market: str
    spot_price: float
    as_of_utc: datetime


def _price_union_sql(catalog: str) -> str:
    return f"""
WITH nem_latest AS (
  SELECT
    'NEM' AS market,
    region_id AS instrument,
    CAST(rrp AS DOUBLE) AS price,
    CAST(LAG(rrp) OVER (PARTITION BY region_id ORDER BY interval_datetime) AS DOUBLE) AS prev_price,
    interval_datetime AS ts,
    ROW_NUMBER() OVER (PARTITION BY region_id ORDER BY interval_datetime DESC) AS rn
  FROM {catalog}.market_nem.prices
),
epex_latest AS (
  SELECT
    'EPEX' AS market,
    bidding_zone AS instrument,
    CAST(price_eur_mwh AS DOUBLE) AS price,
    CAST(LAG(price_eur_mwh) OVER (PARTITION BY bidding_zone ORDER BY delivery_datetime) AS DOUBLE) AS prev_price,
    delivery_datetime AS ts,
    ROW_NUMBER() OVER (PARTITION BY bidding_zone ORDER BY delivery_datetime DESC) AS rn
  FROM {catalog}.market_epex.prices
),
ercot_latest AS (
  SELECT
    'ERCOT' AS market,
    node_id AS instrument,
    CAST(lmp AS DOUBLE) AS price,
    CAST(LAG(lmp) OVER (PARTITION BY node_id ORDER BY interval_datetime) AS DOUBLE) AS prev_price,
    interval_datetime AS ts,
    ROW_NUMBER() OVER (PARTITION BY node_id ORDER BY interval_datetime DESC) AS rn
  FROM {catalog}.market_ercot.lmp
)
SELECT market, instrument, price,
       COALESCE((price - prev_price) / NULLIF(prev_price, 0) * 100.0, 0.0) AS change_pct,
       ts AS timestamp
FROM nem_latest WHERE rn = 1
UNION ALL
SELECT market, instrument, price,
       COALESCE((price - prev_price) / NULLIF(prev_price, 0) * 100.0, 0.0) AS change_pct,
       ts AS timestamp
FROM epex_latest WHERE rn = 1
UNION ALL
SELECT market, instrument, price,
       COALESCE((price - prev_price) / NULLIF(prev_price, 0) * 100.0, 0.0) AS change_pct,
       ts AS timestamp
FROM ercot_latest WHERE rn = 1
ORDER BY market, instrument
"""


@router.get("/current-prices", response_model=APIResponse[list[CurrentPrice]])
async def current_prices() -> APIResponse[list[CurrentPrice]]:
    rows = await execute_sql(_price_union_sql(get_settings().apex_catalog))
    out = [
        CurrentPrice(
            market=str(r.get('market')),
            instrument=str(r.get('instrument')),
            price=float(r.get('price', 0)),
            change_pct=float(r.get('change_pct', 0)),
            timestamp=r.get('timestamp') or datetime.now(timezone.utc),
        )
        for r in rows
    ]
    return APIResponse(data=out, region='GLOBAL')


@router.get("/predispatch", response_model=APIResponse[list[PredispatchPoint]])
async def predispatch(
    market: str = Query(default='NEM'),
    hours: int = Query(default=24, ge=1, le=168),
) -> APIResponse[list[PredispatchPoint]]:
    catalog = get_settings().apex_catalog
    market_key = market.upper()
    await execute_sql(
        f"CREATE TABLE IF NOT EXISTS {catalog}.analytics.price_forecasts ("
        f"market STRING, instrument STRING, forecast_datetime TIMESTAMP, forecast_price DOUBLE, "
        f"forecast_demand_mw DOUBLE, model_name STRING, run_timestamp TIMESTAMP)"
    )
    sql = (
        f"SELECT forecast_datetime AS interval_start, instrument AS region, "
        f"CAST(forecast_price AS DOUBLE) AS forecast_price, CAST(forecast_demand_mw AS DOUBLE) AS forecast_demand_mw "
        f"FROM {catalog}.analytics.price_forecasts "
        f"WHERE upper(market)='{market_key}' "
        f"  AND forecast_datetime <= current_timestamp() + INTERVAL {hours} HOURS "
        f"ORDER BY forecast_datetime ASC"
    )
    rows = await execute_sql(sql)
    out = [
        PredispatchPoint(
            interval_start=r.get('interval_start') or datetime.now(timezone.utc),
            region=str(r.get('region', 'NA')),
            forecast_price=float(r.get('forecast_price', 0)),
            forecast_demand_mw=float(r.get('forecast_demand_mw', 0)),
        )
        for r in rows
    ]
    return APIResponse(data=out, region=market_key)


@router.get("/forward-curves", response_model=APIResponse[list[ForwardCurvePoint]])
async def forward_curves() -> APIResponse[list[ForwardCurvePoint]]:
    catalog = get_settings().apex_catalog
    sql = f"""
WITH base AS (
  SELECT 'NEM' AS hub, CAST(rrp AS DOUBLE) AS px, interval_datetime AS ts
  FROM {catalog}.market_nem.prices
  UNION ALL
  SELECT 'EPEX' AS hub, CAST(price_eur_mwh AS DOUBLE) AS px, delivery_datetime AS ts
  FROM {catalog}.market_epex.prices
  UNION ALL
  SELECT 'ERCOT' AS hub, CAST(lmp AS DOUBLE) AS px, interval_datetime AS ts
  FROM {catalog}.market_ercot.lmp
),
latest AS (
  SELECT hub, px, ts, ROW_NUMBER() OVER (PARTITION BY hub ORDER BY ts DESC) AS rn
  FROM base
)
SELECT 'M+1' AS tenor, hub, AVG(px) AS price FROM latest WHERE rn <= 24 GROUP BY hub
UNION ALL
SELECT 'Q+1' AS tenor, hub, AVG(px) AS price FROM latest WHERE rn <= 24 GROUP BY hub
UNION ALL
SELECT 'CAL+1' AS tenor, hub, AVG(px) AS price FROM latest WHERE rn <= 24 GROUP BY hub
"""
    rows = await execute_sql(sql)
    out = [ForwardCurvePoint(tenor=str(r.get('tenor')), hub=str(r.get('hub')), price=float(r.get('price', 0))) for r in rows]
    return APIResponse(data=out, region='GLOBAL')


@router.get("/summary", response_model=APIResponse[MarketSummary])
async def summary() -> APIResponse[MarketSummary]:
    catalog = get_settings().apex_catalog
    rows = await execute_sql(_price_union_sql(catalog))
    prices = [float(r.get('price', 0)) for r in rows]
    active_markets = len({str(r.get('market')) for r in rows})
    avg = sum(prices) / len(prices) if prices else 0.0
    refresh_rows = await execute_sql(
        f"""
        SELECT MAX(ts) AS last_refresh_utc
        FROM (
          SELECT interval_datetime AS ts FROM {catalog}.market_nem.prices
          UNION ALL
          SELECT delivery_datetime AS ts FROM {catalog}.market_epex.prices
          UNION ALL
          SELECT interval_datetime AS ts FROM {catalog}.market_ercot.lmp
        ) u
        """
    )
    last_refresh = refresh_rows[0].get("last_refresh_utc") if refresh_rows else None
    return APIResponse(
        data=MarketSummary(
            active_markets=active_markets,
            instruments_tracked=len(prices),
            average_price=round(avg, 2),
            last_refresh_utc=last_refresh or datetime.now(timezone.utc),
        ),
        region='GLOBAL',
    )


@router.get("/instrument-quote", response_model=APIResponse[InstrumentQuote])
async def instrument_quote(
    market: str = Query(default='NEM'),
    instrument: str = Query(...),
) -> APIResponse[InstrumentQuote]:
    catalog = get_settings().apex_catalog
    market_key = market.upper()
    instrument_key = instrument.upper()
    if market_key == 'EPEX':
        base = instrument_key.split('_')[0]
        sql = (
            f"WITH x AS ("
            f"  SELECT delivery_datetime AS ts, CAST(price_eur_mwh AS DOUBLE) AS px "
            f"  FROM {catalog}.market_epex.prices WHERE upper(bidding_zone)='{base}'"
            f"), r AS ("
            f"  SELECT px, LAG(px) OVER (ORDER BY ts) AS prev_px, ts, "
            f"         ROW_NUMBER() OVER (ORDER BY ts DESC) AS rn "
            f"  FROM x"
            f") "
            f"SELECT px AS last_price, "
            f"COALESCE((px-prev_px)/NULLIF(prev_px,0)*100,0) AS change_pct, "
            f"px-0.25 AS bid, px+0.25 AS offer, "
            f"CAST((SELECT COUNT(*) FROM x WHERE ts >= current_timestamp() - INTERVAL 24 HOURS) AS DOUBLE) AS volume "
            f"FROM r WHERE rn=1"
        )
    elif market_key == 'ERCOT':
        base = instrument_key.replace('ERCOT_', '')
        sql = (
            f"WITH x AS ("
            f"  SELECT interval_datetime AS ts, CAST(lmp AS DOUBLE) AS px "
            f"  FROM {catalog}.market_ercot.lmp WHERE upper(node_id)='{base}'"
            f"), r AS ("
            f"  SELECT px, LAG(px) OVER (ORDER BY ts) AS prev_px, ts, "
            f"         ROW_NUMBER() OVER (ORDER BY ts DESC) AS rn "
            f"  FROM x"
            f") "
            f"SELECT px AS last_price, "
            f"COALESCE((px-prev_px)/NULLIF(prev_px,0)*100,0) AS change_pct, "
            f"px-0.25 AS bid, px+0.25 AS offer, "
            f"CAST((SELECT COUNT(*) FROM x WHERE ts >= current_timestamp() - INTERVAL 24 HOURS) AS DOUBLE) AS volume "
            f"FROM r WHERE rn=1"
        )
    else:
        base = instrument_key.split('_')[0]
        sql = (
            f"WITH x AS ("
            f"  SELECT interval_datetime AS ts, CAST(rrp AS DOUBLE) AS px "
            f"  FROM {catalog}.market_nem.prices WHERE upper(region_id)='{base}'"
            f"), r AS ("
            f"  SELECT px, LAG(px) OVER (ORDER BY ts) AS prev_px, ts, "
            f"         ROW_NUMBER() OVER (ORDER BY ts DESC) AS rn "
            f"  FROM x"
            f") "
            f"SELECT px AS last_price, "
            f"COALESCE((px-prev_px)/NULLIF(prev_px,0)*100,0) AS change_pct, "
            f"px-0.25 AS bid, px+0.25 AS offer, "
            f"CAST((SELECT COUNT(*) FROM x WHERE ts >= current_timestamp() - INTERVAL 24 HOURS) AS DOUBLE) AS volume "
            f"FROM r WHERE rn=1"
        )
    rows = await execute_sql(sql)
    if not rows:
        raise HTTPException(status_code=404, detail=f"No quote data for {market_key}/{instrument_key}")
    row = rows[0]
    return APIResponse(
        data=InstrumentQuote(
            market=market_key,
            instrument=instrument_key,
            last_price=float(row.get('last_price', 0)),
            change_pct=float(row.get('change_pct', 0)),
            bid=float(row.get('bid', 0)),
            offer=float(row.get('offer', 0)),
            volume=float(row.get('volume', 0)),
            status='OPEN',
        ),
        region=market_key,
    )


@router.get("/forecast-metadata", response_model=APIResponse[ForecastMetadata])
async def forecast_metadata(market: str = Query(default='NEM')) -> APIResponse[ForecastMetadata]:
    catalog = get_settings().apex_catalog
    market_key = market.upper()
    await execute_sql(
        f"CREATE TABLE IF NOT EXISTS {catalog}.analytics.price_forecasts ("
        f"market STRING, instrument STRING, forecast_datetime TIMESTAMP, forecast_price DOUBLE, "
        f"forecast_demand_mw DOUBLE, model_name STRING, run_timestamp TIMESTAMP)"
    )
    sql = (
        f"SELECT "
        f"  upper(market) AS market, "
        f"  max_by(model_name, run_timestamp) AS model_name, "
        f"  MAX(run_timestamp) AS last_run_utc, "
        f"  COUNT(*) AS points_available, "
        f"  MIN(forecast_datetime) AS first_forecast_utc, "
        f"  MAX(forecast_datetime) AS last_forecast_utc "
        f"FROM {catalog}.analytics.price_forecasts "
        f"WHERE upper(market)='{market_key}'"
    )
    rows = await execute_sql(sql)
    if not rows or not rows[0].get("model_name"):
        raise HTTPException(status_code=404, detail=f"No forecast metadata for market {market_key}")
    row = rows[0]
    return APIResponse(
        data=ForecastMetadata(
            market=market_key,
            model_name=str(row.get('model_name')),
            last_run_utc=row.get('last_run_utc'),
            points_available=int(row.get('points_available') or 0),
            first_forecast_utc=row.get('first_forecast_utc'),
            last_forecast_utc=row.get('last_forecast_utc'),
        ),
        region=market_key,
    )


@router.get("/instruments", response_model=APIResponse[list[MarketInstrument]])
async def instruments(market: str = Query(default='NEM')) -> APIResponse[list[MarketInstrument]]:
    catalog = get_settings().apex_catalog
    market_key = market.upper()
    if market_key == "EPEX":
        sql = (
            f"SELECT 'EPEX' AS market, CONCAT(upper(bidding_zone), '_BASE') AS instrument "
            f"FROM {catalog}.market_epex.prices "
            f"GROUP BY bidding_zone ORDER BY instrument"
        )
    elif market_key == "ERCOT":
        sql = (
            f"SELECT 'ERCOT' AS market, CONCAT('ERCOT_', upper(node_id)) AS instrument "
            f"FROM {catalog}.market_ercot.lmp "
            f"GROUP BY node_id ORDER BY instrument"
        )
    else:
        sql = (
            f"SELECT 'NEM' AS market, CONCAT(upper(region_id), '_BASE') AS instrument "
            f"FROM {catalog}.market_nem.prices "
            f"GROUP BY region_id ORDER BY instrument"
        )
    rows = await execute_sql(sql)
    out = [MarketInstrument.model_validate(r) for r in rows]
    return APIResponse(data=out, region=market_key)


@router.get("/spot-price", response_model=APIResponse[SpotPrice])
async def spot_price(market: str = Query(default='NEM')) -> APIResponse[SpotPrice]:
    market_key = market.upper()
    summary_data = (await summary()).data
    rows = await current_prices()
    market_prices = [float(r.price) for r in rows.data if r.market.upper() == market_key]
    if not market_prices:
        raise HTTPException(status_code=404, detail=f"No spot price data for market {market_key}")
    return APIResponse(
        data=SpotPrice(
            market=market_key,
            spot_price=round(sum(market_prices) / len(market_prices), 4),
            as_of_utc=summary_data.last_refresh_utc,
        ),
        region=market_key,
    )
