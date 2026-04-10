"""
Forecasting & Predictive Analytics API Routes
Endpoints for weather, production, volume, and price forecasting data
"""
from __future__ import annotations

from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.backend.config import get_settings
from app.backend.database import execute_sql
from app.backend.models import APIResponse

router = APIRouter(prefix="/api/v1/forecasting", tags=["forecasting"])


# ============================================================================
# Pydantic Models
# ============================================================================

class WeatherForecast(BaseModel):
    forecast_id: str
    region_id: str
    forecast_datetime: datetime
    temperature_celsius: float
    wind_speed_ms: float
    solar_irradiance_wm2: float
    precipitation_mm: float
    humidity_percent: float
    confidence_level: str
    forecast_horizon_hours: int


class WeatherImpact(BaseModel):
    region_id: str
    weather_parameter: str
    price_correlation: float
    price_impact_per_unit: float
    volatility_impact: float
    sample_size: int
    last_updated: datetime | None


class VolumeForecast(BaseModel):
    forecast_id: str
    region_id: str
    forecast_date: str  # DATE as string
    forecast_type: str  # 'BUY' or 'SELL'
    volume_mwh: float
    base_volume_mwh: float
    weather_impact_pct: float
    maintenance_impact_pct: float
    outage_impact_pct: float
    market_demand_factor: float
    confidence_level: str


class ProductionForecast(BaseModel):
    forecast_id: str
    region_id: str
    forecast_datetime: datetime
    asset_type: str
    generation_mw: float
    capacity_mw: float
    efficiency_percent: float
    availability_percent: float
    confidence_level: str
    forecast_horizon_hours: int


class GenerationMix(BaseModel):
    region_id: str
    reading_datetime: datetime
    asset_type: str
    generation_mw: float
    total_generation_mw: float
    mix_percentage: float


class PlantStatus(BaseModel):
    event_id: str
    plant_name: str
    plant_type: str
    region_id: str
    event_type: str
    start_datetime: datetime
    end_datetime: datetime
    capacity_impact_mw: float
    grid_impact: str
    description: str
    status: str


class PriceForecast(BaseModel):
    forecast_id: str
    region_id: str
    instrument: str
    forecast_datetime: datetime
    forecast_price: float
    actual_price: float | None
    error: float | None
    abs_error: float | None
    mape: float | None
    market_type: str
    confidence_level: str
    forecast_horizon_hours: int


class ExtremeEvent(BaseModel):
    event_id: str
    region_id: str
    event_type: str
    severity: str
    start_datetime: datetime
    end_datetime: datetime
    impact_description: str
    price_impact_pct: float
    trading_alert_level: str
    confidence_level: float


class ModelPerformance(BaseModel):
    model_id: str
    model_name: str
    model_type: str
    region_id: str
    mape: float
    mae: float
    rmse: float
    r2_score: float
    bias: float
    evaluation_date: str  # DATE as string
    algorithm: str
    mlflow_run_id: str | None


class VolumeForecastSummary(BaseModel):
    region_id: str
    total_days: int
    buy_days: int
    sell_days: int
    avg_volume_mwh: float
    total_buy_volume_mwh: float
    total_sell_volume_mwh: float


# ============================================================================
# Weather Forecast Endpoints
# ============================================================================

@router.get("/weather", response_model=APIResponse[list[WeatherForecast]])
async def get_weather_forecast(
    region_id: str = Query(default='NSW1'),
    days: int = Query(default=7, ge=1, le=14),
) -> APIResponse[list[WeatherForecast]]:
    """
    Get weather forecast data for a specific region

    Args:
        region_id: NEM region (NSW1, VIC1, QLD1, SA1)
        days: Number of days to forecast (1-14)

    Returns:
        List of weather forecast records
    """
    catalog = get_settings().apex_catalog

    sql = f"""
    SELECT
        forecast_id,
        region_id,
        forecast_datetime,
        CAST(temperature_celsius AS DOUBLE) AS temperature_celsius,
        CAST(wind_speed_ms AS DOUBLE) AS wind_speed_ms,
        CAST(solar_irradiance_wm2 AS DOUBLE) AS solar_irradiance_wm2,
        CAST(precipitation_mm AS DOUBLE) AS precipitation_mm,
        CAST(humidity_percent AS DOUBLE) AS humidity_percent,
        confidence_level,
        CAST(forecast_horizon_hours AS INT) AS forecast_horizon_hours
    FROM {catalog}.forecasting.weather_forecast
    WHERE region_id = '{region_id}'
      AND forecast_datetime <= current_timestamp() + INTERVAL {days} DAYS
      AND forecast_datetime >= current_timestamp()
    ORDER BY forecast_datetime ASC
    """

    rows = await execute_sql(sql)

    out = [WeatherForecast.model_validate(r) for r in rows]
    return APIResponse(data=out, region=region_id)


@router.get("/weather/impact", response_model=APIResponse[list[WeatherImpact]])
async def get_weather_impact(
    region_id: str = Query(default='NSW1'),
) -> APIResponse[list[WeatherImpact]]:
    """
    Get weather impact correlation metrics for price forecasting

    Args:
        region_id: NEM region (NSW1, VIC1, QLD1, SA1)

    Returns:
        Weather impact correlation data
    """
    catalog = get_settings().apex_catalog

    sql = f"""
    SELECT
        region_id,
        weather_parameter,
        CAST(price_correlation AS DOUBLE) AS price_correlation,
        CAST(price_impact_per_unit AS DOUBLE) AS price_impact_per_unit,
        CAST(volatility_impact AS DOUBLE) AS volatility_impact,
        CAST(sample_size AS INT) AS sample_size,
        last_updated
    FROM {catalog}.forecasting.weather_impact
    WHERE region_id = '{region_id}'
    ORDER BY weather_parameter
    """

    rows = await execute_sql(sql)

    if not rows:
        raise HTTPException(
            status_code=404,
            detail=f"No weather impact data found for region {region_id}"
        )

    out = [WeatherImpact.model_validate(r) for r in rows]
    return APIResponse(data=out, region=region_id)


# ============================================================================
# Volume Forecast Endpoints (15-Day BUY/SELL Forecast - KEY FEATURE)
# ============================================================================

@router.get("/volume", response_model=APIResponse[list[VolumeForecast]])
async def get_volume_forecast(
    region_id: str = Query(default='NSW1'),
    days: int = Query(default=15, ge=1, le=15),
) -> APIResponse[list[VolumeForecast]]:
    """
    Get 15-day BUY/SELL volume forecast for energy trading

    This is the KEY feature borrowed from Sahil's demo - provides daily
    forecasts of whether to BUY or SELL energy based on weather, maintenance,
    outages, and market demand factors.

    Args:
        region_id: NEM region (NSW1, VIC1, QLD1, SA1)
        days: Number of days to forecast (1-15)

    Returns:
        List of daily volume forecasts with BUY/SELL recommendations
    """
    catalog = get_settings().apex_catalog

    sql = f"""
    SELECT
        forecast_id,
        region_id,
        CAST(forecast_date AS STRING) AS forecast_date,
        forecast_type,
        CAST(volume_mwh AS DOUBLE) AS volume_mwh,
        CAST(base_volume_mwh AS DOUBLE) AS base_volume_mwh,
        CAST(weather_impact_pct AS DOUBLE) AS weather_impact_pct,
        CAST(maintenance_impact_pct AS DOUBLE) AS maintenance_impact_pct,
        CAST(outage_impact_pct AS DOUBLE) AS outage_impact_pct,
        CAST(market_demand_factor AS DOUBLE) AS market_demand_factor,
        confidence_level
    FROM {catalog}.forecasting.volume_forecast
    WHERE region_id = '{region_id}'
      AND forecast_date <= current_date() + INTERVAL {days} DAYS
      AND forecast_date >= current_date()
    ORDER BY forecast_date ASC
    """

    rows = await execute_sql(sql)

    out = [VolumeForecast.model_validate(r) for r in rows]
    return APIResponse(data=out, region=region_id)


@router.get("/volume/summary", response_model=APIResponse[VolumeForecastSummary])
async def get_volume_forecast_summary(
    region_id: str = Query(default='NSW1'),
    days: int = Query(default=15, ge=1, le=15),
) -> APIResponse[VolumeForecastSummary]:
    """
    Get summary statistics for volume forecast

    Args:
        region_id: NEM region (NSW1, VIC1, QLD1, SA1)
        days: Number of days to analyze (1-15)

    Returns:
        Summary of BUY vs SELL days and volumes
    """
    catalog = get_settings().apex_catalog

    sql = f"""
    WITH forecast_data AS (
        SELECT
            region_id,
            forecast_type,
            CAST(volume_mwh AS DOUBLE) AS volume_mwh
        FROM {catalog}.forecasting.volume_forecast
        WHERE region_id = '{region_id}'
          AND forecast_date <= current_date() + INTERVAL {days} DAYS
          AND forecast_date >= current_date()
    )
    SELECT
        '{region_id}' AS region_id,
        COUNT(*) AS total_days,
        SUM(CASE WHEN forecast_type = 'BUY' THEN 1 ELSE 0 END) AS buy_days,
        SUM(CASE WHEN forecast_type = 'SELL' THEN 1 ELSE 0 END) AS sell_days,
        AVG(volume_mwh) AS avg_volume_mwh,
        SUM(CASE WHEN forecast_type = 'BUY' THEN volume_mwh ELSE 0 END) AS total_buy_volume_mwh,
        SUM(CASE WHEN forecast_type = 'SELL' THEN volume_mwh ELSE 0 END) AS total_sell_volume_mwh
    FROM forecast_data
    """

    rows = await execute_sql(sql)

    if not rows:
        raise HTTPException(
            status_code=404,
            detail=f"No volume forecast data found for region {region_id}"
        )

    row = rows[0]
    summary = VolumeForecastSummary(
        region_id=region_id,
        total_days=int(row.get('total_days', 0)),
        buy_days=int(row.get('buy_days', 0)),
        sell_days=int(row.get('sell_days', 0)),
        avg_volume_mwh=float(row.get('avg_volume_mwh', 0)),
        total_buy_volume_mwh=float(row.get('total_buy_volume_mwh', 0)),
        total_sell_volume_mwh=float(row.get('total_sell_volume_mwh', 0)),
    )

    return APIResponse(data=summary, region=region_id)


# ============================================================================
# Production Forecast Endpoints
# ============================================================================

@router.get("/production", response_model=APIResponse[list[ProductionForecast]])
async def get_production_forecast(
    region_id: str = Query(default='NSW1'),
    asset_type: str | None = Query(default=None),
    days: int = Query(default=7, ge=1, le=14),
) -> APIResponse[list[ProductionForecast]]:
    """
    Get energy production forecast by asset type

    Args:
        region_id: NEM region (NSW1, VIC1, QLD1, SA1)
        asset_type: Filter by asset type (RENEWABLES, COAL, GAS, NUCLEAR, BIOMASS)
        days: Number of days to forecast (1-14)

    Returns:
        List of production forecast records
    """
    catalog = get_settings().apex_catalog

    asset_filter = ""
    if asset_type:
        asset_filter = f"AND asset_type = '{asset_type.upper()}'"

    sql = f"""
    SELECT
        forecast_id,
        region_id,
        forecast_datetime,
        asset_type,
        CAST(generation_mw AS DOUBLE) AS generation_mw,
        CAST(capacity_mw AS DOUBLE) AS capacity_mw,
        CAST(efficiency_percent AS DOUBLE) AS efficiency_percent,
        CAST(availability_percent AS DOUBLE) AS availability_percent,
        confidence_level,
        CAST(forecast_horizon_hours AS INT) AS forecast_horizon_hours
    FROM {catalog}.forecasting.production_forecast
    WHERE region_id = '{region_id}'
      {asset_filter}
      AND forecast_datetime <= current_timestamp() + INTERVAL {days} DAYS
      AND forecast_datetime >= current_timestamp()
    ORDER BY forecast_datetime ASC, asset_type
    """

    rows = await execute_sql(sql)

    out = [ProductionForecast.model_validate(r) for r in rows]
    return APIResponse(data=out, region=region_id)


@router.get("/generation-mix", response_model=APIResponse[list[GenerationMix]])
async def get_generation_mix(
    region_id: str = Query(default='NSW1'),
    hours: int = Query(default=24, ge=1, le=168),
) -> APIResponse[list[GenerationMix]]:
    """
    Get historical generation mix for trending

    Args:
        region_id: NEM region (NSW1, VIC1, QLD1, SA1)
        hours: Number of hours of historical data (1-168)

    Returns:
        Generation mix historical data
    """
    catalog = get_settings().apex_catalog

    sql = f"""
    SELECT
        region_id,
        reading_datetime,
        asset_type,
        CAST(generation_mw AS DOUBLE) AS generation_mw,
        CAST(total_generation_mw AS DOUBLE) AS total_generation_mw,
        CAST(mix_percentage AS DOUBLE) AS mix_percentage
    FROM {catalog}.forecasting.generation_mix_historical
    WHERE region_id = '{region_id}'
      AND reading_datetime >= current_timestamp() - INTERVAL {hours} HOURS
    ORDER BY reading_datetime DESC, asset_type
    """

    rows = await execute_sql(sql)

    out = [GenerationMix.model_validate(r) for r in rows]
    return APIResponse(data=out, region=region_id)


# ============================================================================
# Plant Status Endpoints
# ============================================================================

@router.get("/plant-status", response_model=APIResponse[list[PlantStatus]])
async def get_plant_status(
    region_id: str = Query(default='NSW1'),
    event_type: str | None = Query(default=None),
    days: int = Query(default=14, ge=1, le=30),
) -> APIResponse[list[PlantStatus]]:
    """
    Get plant outages, maintenance, and ramp schedules

    Used for Plant Status Timeline (Gantt chart) visualization

    Args:
        region_id: NEM region (NSW1, VIC1, QLD1, SA1)
        event_type: Filter by event type (OUTAGE, MAINTENANCE, RAMP_UP, RAMP_DOWN)
        days: Number of days to forecast (1-30)

    Returns:
        List of plant status events
    """
    catalog = get_settings().apex_catalog

    event_filter = ""
    if event_type:
        event_filter = f"AND event_type = '{event_type.upper()}'"

    sql = f"""
    SELECT
        event_id,
        plant_name,
        plant_type,
        region_id,
        event_type,
        start_datetime,
        end_datetime,
        CAST(capacity_impact_mw AS DOUBLE) AS capacity_impact_mw,
        grid_impact,
        description,
        status
    FROM {catalog}.forecasting.plant_status
    WHERE region_id = '{region_id}'
      {event_filter}
      AND start_datetime <= current_timestamp() + INTERVAL {days} DAYS
      AND end_datetime >= current_timestamp()
    ORDER BY start_datetime ASC
    """

    rows = await execute_sql(sql)

    out = [PlantStatus.model_validate(r) for r in rows]
    return APIResponse(data=out, region=region_id)


# ============================================================================
# Price Forecast Endpoints
# ============================================================================

@router.get("/price", response_model=APIResponse[list[PriceForecast]])
async def get_price_forecast(
    region_id: str = Query(default='NSW1'),
    market_type: str = Query(default='DAY_AHEAD'),
    hours: int = Query(default=24, ge=1, le=168),
) -> APIResponse[list[PriceForecast]]:
    """
    Get energy price forecasts with actuals for validation

    Args:
        region_id: NEM region (NSW1, VIC1, QLD1, SA1)
        market_type: Market type (DAY_AHEAD, INTRADAY, IMBALANCE)
        hours: Number of hours to forecast (1-168)

    Returns:
        List of price forecast records
    """
    catalog = get_settings().apex_catalog

    sql = f"""
    SELECT
        forecast_id,
        region_id,
        instrument,
        forecast_datetime,
        CAST(forecast_price AS DOUBLE) AS forecast_price,
        CAST(actual_price AS DOUBLE) AS actual_price,
        CAST(error AS DOUBLE) AS error,
        CAST(abs_error AS DOUBLE) AS abs_error,
        CAST(mape AS DOUBLE) AS mape,
        market_type,
        confidence_level,
        CAST(forecast_horizon_hours AS INT) AS forecast_horizon_hours
    FROM {catalog}.forecasting.price_forecast
    WHERE region_id = '{region_id}'
      AND market_type = '{market_type.upper()}'
      AND forecast_datetime <= current_timestamp() + INTERVAL {hours} HOURS
      AND forecast_datetime >= current_timestamp()
    ORDER BY forecast_datetime ASC
    """

    rows = await execute_sql(sql)

    out = [PriceForecast.model_validate(r) for r in rows]
    return APIResponse(data=out, region=region_id)


# ============================================================================
# Extreme Events Endpoints
# ============================================================================

@router.get("/extreme-events", response_model=APIResponse[list[ExtremeEvent]])
async def get_extreme_events(
    region_id: str = Query(default='NSW1'),
    severity: str | None = Query(default=None),
) -> APIResponse[list[ExtremeEvent]]:
    """
    Get extreme weather events impacting trading

    Args:
        region_id: NEM region (NSW1, VIC1, QLD1, SA1)
        severity: Filter by severity (HIGH, MEDIUM, LOW)

    Returns:
        List of extreme weather events
    """
    catalog = get_settings().apex_catalog

    severity_filter = ""
    if severity:
        severity_filter = f"AND severity = '{severity.upper()}'"

    sql = f"""
    SELECT
        event_id,
        region_id,
        event_type,
        severity,
        start_datetime,
        end_datetime,
        impact_description,
        CAST(price_impact_pct AS DOUBLE) AS price_impact_pct,
        trading_alert_level,
        CAST(confidence_level AS DOUBLE) AS confidence_level
    FROM {catalog}.forecasting.extreme_events
    WHERE region_id = '{region_id}'
      {severity_filter}
      AND end_datetime >= current_timestamp()
    ORDER BY start_datetime ASC
    """

    rows = await execute_sql(sql)

    out = [ExtremeEvent.model_validate(r) for r in rows]
    return APIResponse(data=out, region=region_id)


# ============================================================================
# Model Performance Endpoints
# ============================================================================

@router.get("/model-performance", response_model=APIResponse[list[ModelPerformance]])
async def get_model_performance(
    model_type: str | None = Query(default=None),
    region_id: str | None = Query(default=None),
) -> APIResponse[list[ModelPerformance]]:
    """
    Get model performance metrics for MLflow integration

    Args:
        model_type: Filter by model type (WEATHER, PRICE, PRODUCTION, VOLUME)
        region_id: Filter by NEM region (NSW1, VIC1, QLD1, SA1)

    Returns:
        List of model performance metrics
    """
    catalog = get_settings().apex_catalog

    filters = []
    if model_type:
        filters.append(f"model_type = '{model_type.upper()}'")
    if region_id:
        filters.append(f"region_id = '{region_id}'")

    where_clause = ""
    if filters:
        where_clause = "WHERE " + " AND ".join(filters)

    sql = f"""
    SELECT
        model_id,
        model_name,
        model_type,
        region_id,
        CAST(mape AS DOUBLE) AS mape,
        CAST(mae AS DOUBLE) AS mae,
        CAST(rmse AS DOUBLE) AS rmse,
        CAST(r2_score AS DOUBLE) AS r2_score,
        CAST(bias AS DOUBLE) AS bias,
        CAST(evaluation_date AS STRING) AS evaluation_date,
        algorithm,
        mlflow_run_id
    FROM {catalog}.forecasting.model_performance
    {where_clause}
    ORDER BY evaluation_date DESC
    LIMIT 100
    """

    rows = await execute_sql(sql)

    out = [ModelPerformance.model_validate(r) for r in rows]
    return APIResponse(data=out, region=region_id or 'GLOBAL')
