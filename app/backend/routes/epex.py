"""
EPEX Market Data Routes
Real-time EPEX market data ingestion and query endpoints
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel

from app.backend.config import get_settings
from app.backend.database import execute_sql
from app.backend.models import APIResponse
from app.backend.epex.ingestion import get_epex_ingestion_service

router = APIRouter(prefix="/api/v1/epex", tags=["epex"])


class DayAheadPrice(BaseModel):
    market_area: str
    delivery_date: str
    delivery_hour: int
    delivery_start: datetime
    delivery_end: datetime
    price_eur_mwh: float
    volume_mwh: Optional[float]


class GenerationForecast(BaseModel):
    market_area: str
    forecast_timestamp: datetime
    delivery_start: datetime
    delivery_end: datetime
    fuel_type: str
    forecasted_mw: float


class DemandForecast(BaseModel):
    market_area: str
    forecast_timestamp: datetime
    delivery_start: datetime
    delivery_end: datetime
    forecasted_demand_mw: float


class CrossBorderFlow(BaseModel):
    from_area: str
    to_area: str
    timestamp: datetime
    scheduled_flow_mw: float
    actual_flow_mw: Optional[float]


class IngestionStatus(BaseModel):
    status: str
    records_loaded: int
    market_area: Optional[str] = None
    fuel_type: Optional[str] = None
    date: Optional[str] = None


class MarketArea(BaseModel):
    code: str
    name: str


# EPEX Market Areas
MARKET_AREAS = [
    {"code": "DE", "name": "Germany/Luxembourg"},
    {"code": "FR", "name": "France"},
    {"code": "AT", "name": "Austria"},
    {"code": "NL", "name": "Netherlands"},
    {"code": "BE", "name": "Belgium"},
    {"code": "CH", "name": "Switzerland"},
    {"code": "IT", "name": "Italy"},
    {"code": "ES", "name": "Spain"},
    {"code": "DK", "name": "Denmark"},
    {"code": "NO", "name": "Norway"},
]


@router.get("/market-areas", response_model=APIResponse[list[MarketArea]])
async def get_market_areas() -> APIResponse[list[MarketArea]]:
    """Get list of supported EPEX market areas"""
    return APIResponse(
        data=[MarketArea(**area) for area in MARKET_AREAS],
        region="EPEX"
    )


@router.get("/day-ahead-prices", response_model=APIResponse[list[DayAheadPrice]])
async def get_day_ahead_prices(
    market_area: str = Query("DE", description="Market area code"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    limit: int = Query(100, ge=1, le=1000)
) -> APIResponse[list[DayAheadPrice]]:
    """Get EPEX day-ahead prices for a market area"""
    catalog = get_settings().apex_catalog

    # Default to last 7 days if no dates provided
    if not start_date:
        start_date = (datetime.now() - timedelta(days=7)).date().isoformat()
    if not end_date:
        end_date = datetime.now().date().isoformat()

    sql = f"""
    SELECT
        market_area,
        delivery_date,
        delivery_hour,
        delivery_start,
        delivery_end,
        price_eur_mwh,
        volume_mwh
    FROM {catalog}.market_epex.day_ahead_prices
    WHERE market_area = '{market_area.upper()}'
      AND delivery_date >= DATE'{start_date}'
      AND delivery_date <= DATE'{end_date}'
    ORDER BY delivery_start DESC
    LIMIT {limit}
    """

    try:
        rows = await execute_sql(sql)
        data = [
            DayAheadPrice(
                market_area=r['market_area'],
                delivery_date=str(r['delivery_date']),
                delivery_hour=int(r['delivery_hour']),
                delivery_start=r['delivery_start'],
                delivery_end=r['delivery_end'],
                price_eur_mwh=float(r['price_eur_mwh']),
                volume_mwh=float(r['volume_mwh']) if r['volume_mwh'] else None
            )
            for r in rows
        ]
        return APIResponse(data=data, region="EPEX")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch day-ahead prices: {str(e)}")


@router.get("/generation-forecasts", response_model=APIResponse[list[GenerationForecast]])
async def get_generation_forecasts(
    market_area: str = Query("DE", description="Market area code"),
    fuel_type: str = Query("SOLAR", description="Fuel type (SOLAR, WIND_ONSHORE, etc.)"),
    hours_ahead: int = Query(24, ge=1, le=168)
) -> APIResponse[list[GenerationForecast]]:
    """Get generation forecasts for specific fuel type"""
    catalog = get_settings().apex_catalog

    sql = f"""
    SELECT
        market_area,
        forecast_timestamp,
        delivery_start,
        delivery_end,
        fuel_type,
        forecasted_mw
    FROM {catalog}.market_epex.generation_forecasts
    WHERE market_area = '{market_area.upper()}'
      AND fuel_type = '{fuel_type.upper()}'
      AND delivery_start >= CURRENT_TIMESTAMP()
      AND delivery_start <= CURRENT_TIMESTAMP() + INTERVAL {hours_ahead} HOURS
    ORDER BY delivery_start ASC
    """

    try:
        rows = await execute_sql(sql)
        data = [GenerationForecast(**r) for r in rows]
        return APIResponse(data=data, region="EPEX")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch generation forecasts: {str(e)}")


@router.get("/demand-forecasts", response_model=APIResponse[list[DemandForecast]])
async def get_demand_forecasts(
    market_area: str = Query("DE", description="Market area code"),
    hours_ahead: int = Query(48, ge=1, le=168)
) -> APIResponse[list[DemandForecast]]:
    """Get demand forecasts for a market area"""
    catalog = get_settings().apex_catalog

    sql = f"""
    SELECT
        market_area,
        forecast_timestamp,
        delivery_start,
        delivery_end,
        forecasted_demand_mw
    FROM {catalog}.market_epex.demand_forecasts
    WHERE market_area = '{market_area.upper()}'
      AND delivery_start >= CURRENT_TIMESTAMP()
      AND delivery_start <= CURRENT_TIMESTAMP() + INTERVAL {hours_ahead} HOURS
    ORDER BY delivery_start ASC
    """

    try:
        rows = await execute_sql(sql)
        data = [DemandForecast(**r) for r in rows]
        return APIResponse(data=data, region="EPEX")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch demand forecasts: {str(e)}")


@router.get("/cross-border-flows", response_model=APIResponse[list[CrossBorderFlow]])
async def get_cross_border_flows(
    from_area: Optional[str] = Query(None, description="From area code"),
    to_area: Optional[str] = Query(None, description="To area code"),
    hours: int = Query(24, ge=1, le=168)
) -> APIResponse[list[CrossBorderFlow]]:
    """Get cross-border flow data"""
    catalog = get_settings().apex_catalog

    where_clauses = []
    if from_area:
        where_clauses.append(f"from_area = '{from_area.upper()}'")
    if to_area:
        where_clauses.append(f"to_area = '{to_area.upper()}'")

    where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

    sql = f"""
    SELECT
        from_area,
        to_area,
        timestamp,
        scheduled_flow_mw,
        actual_flow_mw
    FROM {catalog}.market_epex.cross_border_flows
    WHERE {where_sql}
      AND timestamp >= CURRENT_TIMESTAMP() - INTERVAL {hours} HOURS
    ORDER BY timestamp DESC
    """

    try:
        rows = await execute_sql(sql)
        data = [CrossBorderFlow(**r) for r in rows]
        return APIResponse(data=data, region="EPEX")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch cross-border flows: {str(e)}")


# Ingestion endpoints
@router.post("/ingest/day-ahead-prices", response_model=APIResponse[IngestionStatus])
async def ingest_day_ahead_prices(
    background_tasks: BackgroundTasks,
    market_area: str = Query("DE", description="Market area code"),
    date: Optional[str] = Query(None, description="Date to ingest (YYYY-MM-DD)")
) -> APIResponse[IngestionStatus]:
    """
    Trigger day-ahead price ingestion for a market area

    NOTE: This endpoint requires ENTSOE API key to be configured
    """
    service = get_epex_ingestion_service()

    target_date = datetime.fromisoformat(date) if date else None

    try:
        result = await service.ingest_day_ahead_prices(market_area, target_date)
        return APIResponse(
            data=IngestionStatus(**result),
            region="EPEX"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")


@router.post("/ingest/generation-forecast", response_model=APIResponse[IngestionStatus])
async def ingest_generation_forecast(
    background_tasks: BackgroundTasks,
    market_area: str = Query("DE", description="Market area code"),
    fuel_type: str = Query("SOLAR", description="Fuel type"),
    date: Optional[str] = Query(None, description="Date to ingest (YYYY-MM-DD)")
) -> APIResponse[IngestionStatus]:
    """
    Trigger generation forecast ingestion

    NOTE: This endpoint requires ENTSOE API key to be configured
    """
    service = get_epex_ingestion_service()

    target_date = datetime.fromisoformat(date) if date else None

    try:
        result = await service.ingest_generation_forecast(market_area, fuel_type, target_date)
        return APIResponse(
            data=IngestionStatus(**result),
            region="EPEX"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")


@router.post("/ingest/load-forecast", response_model=APIResponse[IngestionStatus])
async def ingest_load_forecast(
    background_tasks: BackgroundTasks,
    market_area: str = Query("DE", description="Market area code"),
    date: Optional[str] = Query(None, description="Date to ingest (YYYY-MM-DD)")
) -> APIResponse[IngestionStatus]:
    """
    Trigger load forecast ingestion

    NOTE: This endpoint requires ENTSOE API key to be configured
    """
    service = get_epex_ingestion_service()

    target_date = datetime.fromisoformat(date) if date else None

    try:
        result = await service.ingest_load_forecast(market_area, target_date)
        return APIResponse(
            data=IngestionStatus(**result),
            region="EPEX"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")
