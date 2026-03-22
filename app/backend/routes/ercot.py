"""
ERCOT Market Data Routes
Real-time ERCOT market data ingestion and query endpoints
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel

from app.backend.config import get_settings
from app.backend.database import execute_sql
from app.backend.models import APIResponse
from app.backend.ercot.ingestion import get_ercot_ingestion_service

router = APIRouter(prefix="/api/v1/ercot", tags=["ercot"])


class RealTimePrice(BaseModel):
    settlement_point: str
    interval_datetime: datetime
    spp_usd_mwh: float
    congestion_price_usd_mwh: float
    loss_price_usd_mwh: float


class DayAheadPrice(BaseModel):
    settlement_point: str
    delivery_date: str
    delivery_hour: int
    delivery_interval: int
    delivery_start: datetime
    lmp_usd_mwh: float
    energy_price_usd_mwh: float
    congestion_price_usd_mwh: float
    loss_price_usd_mwh: float


class LoadForecast(BaseModel):
    forecast_type: str
    forecast_timestamp: datetime
    delivery_start: datetime
    delivery_end: datetime
    forecasted_load_mw: float


class RenewableGeneration(BaseModel):
    timestamp: datetime
    fuel_type: str
    actual_generation_mw: float
    installed_capacity_mw: float
    capacity_factor: float


class IngestionStatus(BaseModel):
    status: str
    records_loaded: int
    settlement_point: Optional[str] = None
    fuel_type: Optional[str] = None
    delivery_date: Optional[str] = None
    interval: Optional[str] = None


class SettlementPoint(BaseModel):
    code: str
    name: str
    zone: str


# ERCOT Settlement Points
SETTLEMENT_POINTS = [
    {"code": "HB_BUSAVG", "name": "System-wide Average", "zone": "ERCOT"},
    {"code": "HB_NORTH", "name": "North Hub", "zone": "NORTH"},
    {"code": "HB_SOUTH", "name": "South Hub", "zone": "SOUTH"},
    {"code": "HB_WEST", "name": "West Hub", "zone": "WEST"},
    {"code": "HB_HOUSTON", "name": "Houston Hub", "zone": "COAST"},
    {"code": "HB_PAN", "name": "Panhandle Hub", "zone": "PANHANDLE"},
]


@router.get("/settlement-points", response_model=APIResponse[list[SettlementPoint]])
async def get_settlement_points() -> APIResponse[list[SettlementPoint]]:
    """Get list of ERCOT settlement points"""
    return APIResponse(
        data=[SettlementPoint(**sp) for sp in SETTLEMENT_POINTS],
        region="ERCOT"
    )


@router.get("/real-time-prices", response_model=APIResponse[list[RealTimePrice]])
async def get_real_time_prices(
    settlement_point: str = Query("HB_BUSAVG", description="Settlement point code"),
    hours: int = Query(24, ge=1, le=168, description="Hours of history"),
    limit: int = Query(288, ge=1, le=2000, description="Max records (12 per hour)")
) -> APIResponse[list[RealTimePrice]]:
    """
    Get ERCOT real-time Settlement Point Prices (SPP)

    Data is at 5-minute intervals (12 intervals per hour)
    """
    catalog = get_settings().apex_catalog

    sql = f"""
    SELECT
        settlement_point,
        interval_datetime,
        spp_usd_mwh,
        congestion_price_usd_mwh,
        loss_price_usd_mwh
    FROM {catalog}.market_ercot.real_time_prices
    WHERE settlement_point = '{settlement_point.upper()}'
      AND interval_datetime >= CURRENT_TIMESTAMP() - INTERVAL {hours} HOURS
    ORDER BY interval_datetime DESC
    LIMIT {limit}
    """

    try:
        rows = await execute_sql(sql)
        data = [RealTimePrice(**r) for r in rows]
        return APIResponse(data=data, region="ERCOT")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch real-time prices: {str(e)}")


@router.get("/day-ahead-prices", response_model=APIResponse[list[DayAheadPrice]])
async def get_day_ahead_prices(
    settlement_point: str = Query("HB_BUSAVG", description="Settlement point code"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    limit: int = Query(100, ge=1, le=1000)
) -> APIResponse[list[DayAheadPrice]]:
    """Get ERCOT day-ahead market (DAM) prices"""
    catalog = get_settings().apex_catalog

    # Default to last 7 days if no dates provided
    if not start_date:
        start_date = (datetime.now() - timedelta(days=7)).date().isoformat()
    if not end_date:
        end_date = datetime.now().date().isoformat()

    sql = f"""
    SELECT
        settlement_point,
        delivery_date,
        delivery_hour,
        delivery_interval,
        delivery_start,
        lmp_usd_mwh,
        energy_price_usd_mwh,
        congestion_price_usd_mwh,
        loss_price_usd_mwh
    FROM {catalog}.market_ercot.day_ahead_prices
    WHERE settlement_point = '{settlement_point.upper()}'
      AND delivery_date >= DATE'{start_date}'
      AND delivery_date <= DATE'{end_date}'
    ORDER BY delivery_start DESC
    LIMIT {limit}
    """

    try:
        rows = await execute_sql(sql)
        data = [
            DayAheadPrice(
                settlement_point=r['settlement_point'],
                delivery_date=str(r['delivery_date']),
                delivery_hour=int(r['delivery_hour']),
                delivery_interval=int(r['delivery_interval']),
                delivery_start=r['delivery_start'],
                lmp_usd_mwh=float(r['lmp_usd_mwh']),
                energy_price_usd_mwh=float(r['energy_price_usd_mwh']),
                congestion_price_usd_mwh=float(r['congestion_price_usd_mwh']),
                loss_price_usd_mwh=float(r['loss_price_usd_mwh'])
            )
            for r in rows
        ]
        return APIResponse(data=data, region="ERCOT")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch day-ahead prices: {str(e)}")


@router.get("/load-forecasts", response_model=APIResponse[list[LoadForecast]])
async def get_load_forecasts(
    forecast_type: str = Query("SHORT_TERM", description="Forecast type (SHORT_TERM, MID_TERM, LONG_TERM)"),
    hours_ahead: int = Query(168, ge=1, le=720)
) -> APIResponse[list[LoadForecast]]:
    """Get ERCOT system load forecasts"""
    catalog = get_settings().apex_catalog

    sql = f"""
    SELECT
        forecast_type,
        forecast_timestamp,
        delivery_start,
        delivery_end,
        forecasted_load_mw
    FROM {catalog}.market_ercot.load_forecasts
    WHERE forecast_type = '{forecast_type.upper()}'
      AND delivery_start >= CURRENT_TIMESTAMP()
      AND delivery_start <= CURRENT_TIMESTAMP() + INTERVAL {hours_ahead} HOURS
    ORDER BY delivery_start ASC
    """

    try:
        rows = await execute_sql(sql)
        data = [LoadForecast(**r) for r in rows]
        return APIResponse(data=data, region="ERCOT")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch load forecasts: {str(e)}")


@router.get("/renewable-generation", response_model=APIResponse[list[RenewableGeneration]])
async def get_renewable_generation(
    fuel_type: str = Query("WIND", description="Fuel type (WIND, SOLAR)"),
    hours: int = Query(24, ge=1, le=168)
) -> APIResponse[list[RenewableGeneration]]:
    """Get actual renewable generation data"""
    catalog = get_settings().apex_catalog

    sql = f"""
    SELECT
        timestamp,
        fuel_type,
        actual_generation_mw,
        installed_capacity_mw,
        capacity_factor
    FROM {catalog}.market_ercot.renewable_generation
    WHERE fuel_type = '{fuel_type.upper()}'
      AND timestamp >= CURRENT_TIMESTAMP() - INTERVAL {hours} HOURS
    ORDER BY timestamp DESC
    """

    try:
        rows = await execute_sql(sql)
        data = [RenewableGeneration(**r) for r in rows]
        return APIResponse(data=data, region="ERCOT")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch renewable generation: {str(e)}")


# Ingestion endpoints
@router.post("/ingest/real-time-prices", response_model=APIResponse[IngestionStatus])
async def ingest_real_time_prices(
    background_tasks: BackgroundTasks,
    settlement_point: str = Query("HB_BUSAVG", description="Settlement point code"),
    lookback_hours: int = Query(1, ge=1, le=24, description="Hours to fetch")
) -> APIResponse[IngestionStatus]:
    """
    Trigger real-time price ingestion (5-minute SPP)

    NOTE: This endpoint may require ERCOT API credentials
    """
    service = get_ercot_ingestion_service()

    try:
        result = await service.ingest_real_time_prices(settlement_point, lookback_hours)
        return APIResponse(
            data=IngestionStatus(**result),
            region="ERCOT"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")


@router.post("/ingest/day-ahead-prices", response_model=APIResponse[IngestionStatus])
async def ingest_day_ahead_prices(
    background_tasks: BackgroundTasks,
    settlement_point: str = Query("HB_BUSAVG", description="Settlement point code"),
    delivery_date: Optional[str] = Query(None, description="Delivery date (YYYY-MM-DD)")
) -> APIResponse[IngestionStatus]:
    """
    Trigger day-ahead price ingestion

    NOTE: This endpoint may require ERCOT API credentials
    """
    service = get_ercot_ingestion_service()

    target_date = datetime.fromisoformat(delivery_date).date() if delivery_date else None

    try:
        result = await service.ingest_day_ahead_prices(settlement_point, target_date)
        return APIResponse(
            data=IngestionStatus(**result),
            region="ERCOT"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")


@router.post("/ingest/load-forecast", response_model=APIResponse[IngestionStatus])
async def ingest_load_forecast(
    background_tasks: BackgroundTasks,
    forecast_type: str = Query("SHORT_TERM", description="Forecast type")
) -> APIResponse[IngestionStatus]:
    """
    Trigger load forecast ingestion

    NOTE: This endpoint may require ERCOT API credentials
    """
    service = get_ercot_ingestion_service()

    try:
        result = await service.ingest_load_forecast(forecast_type)
        return APIResponse(
            data=IngestionStatus(**result),
            region="ERCOT"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")


@router.post("/ingest/renewable-generation", response_model=APIResponse[IngestionStatus])
async def ingest_renewable_generation(
    background_tasks: BackgroundTasks,
    fuel_type: str = Query("WIND", description="Fuel type (WIND, SOLAR)"),
    date: Optional[str] = Query(None, description="Date to ingest (YYYY-MM-DD)")
) -> APIResponse[IngestionStatus]:
    """
    Trigger renewable generation data ingestion

    NOTE: This endpoint may require ERCOT API credentials
    """
    service = get_ercot_ingestion_service()

    target_date = datetime.fromisoformat(date).date() if date else None

    try:
        result = await service.ingest_renewable_generation(fuel_type, target_date)
        return APIResponse(
            data=IngestionStatus(**result),
            region="ERCOT"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")
