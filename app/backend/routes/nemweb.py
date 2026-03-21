"""
NEMWEB Data Ingestion API Routes
Trigger ingestion jobs, monitor status, view data quality
"""
from __future__ import annotations

from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

from app.backend.config import get_settings
from app.backend.database import execute_sql
from app.backend.models import APIResponse
from app.backend.nemweb.ingestion import get_ingestion_service
from app.backend.nemweb.data_quality import get_quality_validator

router = APIRouter(prefix="/api/v1/nemweb", tags=["nemweb"])

# ============================================================================
# Pydantic Models
# ============================================================================

class IngestionTriggerRequest(BaseModel):
    data_type: str  # 'DISPATCH_PRICES', 'PREDISPATCH', 'DEMAND'
    region_id: str = 'NSW1'
    date: Optional[str] = None  # YYYY-MM-DD (default: today)


class BackfillRequest(BaseModel):
    region_id: str = 'NSW1'
    start_date: str  # YYYY-MM-DD
    end_date: str  # YYYY-MM-DD


class IngestionLogInfo(BaseModel):
    log_id: str
    data_type: str
    date_loaded: str
    region_id: str
    records_loaded: int
    records_failed: int
    start_timestamp: str
    end_timestamp: Optional[str]
    duration_seconds: Optional[float]
    status: str
    error_message: Optional[str]


class DataFreshnessInfo(BaseModel):
    data_type: str
    region_id: str
    latest_data_timestamp: Optional[str]
    minutes_since_latest: Optional[int]
    total_records: int
    last_ingestion_timestamp: Optional[str]


class QualityMetricInfo(BaseModel):
    metric_id: str
    check_timestamp: str
    data_type: str
    region_id: str
    date_checked: str
    metric_name: str
    metric_value: float
    threshold_value: float
    passed: bool
    details: str


# ============================================================================
# Ingestion Endpoints
# ============================================================================

@router.post("/ingest/trigger")
async def trigger_ingestion(
    request: IngestionTriggerRequest,
    background_tasks: BackgroundTasks,
) -> APIResponse[Dict[str, Any]]:
    """
    Trigger NEMWEB data ingestion job

    Args:
        request: Ingestion configuration

    Returns:
        Job trigger confirmation
    """
    service = get_ingestion_service()

    # Parse date
    if request.date:
        date = datetime.fromisoformat(request.date)
    else:
        date = datetime.now()

    # Trigger appropriate ingestion in background
    if request.data_type == 'DISPATCH_PRICES':
        background_tasks.add_task(
            service.ingest_dispatch_prices,
            date=date,
            regions=[request.region_id],
        )
    elif request.data_type == 'PREDISPATCH':
        background_tasks.add_task(
            service.ingest_predispatch_forecasts,
            region_id=request.region_id,
            hours=24,
        )
    elif request.data_type == 'DEMAND':
        background_tasks.add_task(
            service.ingest_demand_actual,
            region_id=request.region_id,
            date=date,
        )
    else:
        raise HTTPException(status_code=400, detail=f'Unknown data type: {request.data_type}')

    return APIResponse(data={
        'status': 'TRIGGERED',
        'data_type': request.data_type,
        'region_id': request.region_id,
        'date': date.isoformat(),
        'message': 'Ingestion job started in background',
    })


@router.post("/backfill/trigger")
async def trigger_backfill(
    request: BackfillRequest,
    background_tasks: BackgroundTasks,
) -> APIResponse[Dict[str, Any]]:
    """
    Trigger historical data backfill

    Args:
        request: Backfill configuration

    Returns:
        Backfill trigger confirmation
    """
    service = get_ingestion_service()

    start_date = datetime.fromisoformat(request.start_date)
    end_date = datetime.fromisoformat(request.end_date)

    # Validate date range
    days = (end_date - start_date).days
    if days > 365:
        raise HTTPException(status_code=400, detail='Backfill limited to 365 days')

    if days < 0:
        raise HTTPException(status_code=400, detail='End date must be after start date')

    # Trigger backfill in background
    background_tasks.add_task(
        service.backfill_historical_prices,
        start_date=start_date,
        end_date=end_date,
        region_id=request.region_id,
    )

    return APIResponse(data={
        'status': 'TRIGGERED',
        'region_id': request.region_id,
        'start_date': request.start_date,
        'end_date': request.end_date,
        'days': days,
        'message': f'Backfill job started for {days} days',
    })


@router.get("/ingest/logs", response_model=APIResponse[List[IngestionLogInfo]])
async def get_ingestion_logs(
    data_type: Optional[str] = Query(default=None),
    region_id: Optional[str] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
) -> APIResponse[List[IngestionLogInfo]]:
    """
    Get ingestion logs

    Args:
        data_type: Filter by data type
        region_id: Filter by region
        limit: Number of logs

    Returns:
        List of ingestion logs
    """
    catalog = get_settings().apex_catalog

    filters = []
    if data_type:
        filters.append(f"data_type = '{data_type}'")
    if region_id:
        filters.append(f"region_id = '{region_id}'")

    where_clause = f"WHERE {' AND '.join(filters)}" if filters else ""

    sql = f"""
    SELECT
        log_id,
        data_type,
        CAST(date_loaded AS STRING) AS date_loaded,
        region_id,
        CAST(records_loaded AS INT) AS records_loaded,
        CAST(records_failed AS INT) AS records_failed,
        CAST(start_timestamp AS STRING) AS start_timestamp,
        CAST(end_timestamp AS STRING) AS end_timestamp,
        duration_seconds,
        status,
        error_message
    FROM {catalog}.nemweb.ingestion_log
    {where_clause}
    ORDER BY start_timestamp DESC
    LIMIT {limit}
    """

    rows = await execute_sql(sql)
    logs = [IngestionLogInfo.model_validate(r) for r in rows]

    return APIResponse(data=logs)


# ============================================================================
# Monitoring Endpoints
# ============================================================================

@router.get("/monitor/freshness", response_model=APIResponse[List[DataFreshnessInfo]])
async def get_data_freshness() -> APIResponse[List[DataFreshnessInfo]]:
    """
    Get data freshness for all data types

    Returns:
        List of data freshness info
    """
    catalog = get_settings().apex_catalog

    sql = f"""
    SELECT
        data_type,
        region_id,
        CAST(latest_data_timestamp AS STRING) AS latest_data_timestamp,
        CAST(minutes_since_latest AS INT) AS minutes_since_latest,
        CAST(total_records AS INT) AS total_records,
        CAST(last_ingestion_timestamp AS STRING) AS last_ingestion_timestamp
    FROM {catalog}.nemweb.data_freshness
    ORDER BY data_type, region_id
    """

    rows = await execute_sql(sql)
    freshness = [DataFreshnessInfo.model_validate(r) for r in rows]

    return APIResponse(data=freshness)


@router.get("/monitor/summary")
async def get_ingestion_summary(
    days: int = Query(default=7, ge=1, le=90),
) -> APIResponse[List[Dict[str, Any]]]:
    """
    Get ingestion summary statistics

    Args:
        days: Number of days to include

    Returns:
        Summary statistics
    """
    catalog = get_settings().apex_catalog

    sql = f"""
    SELECT
        CAST(ingestion_date AS STRING) AS ingestion_date,
        data_type,
        region_id,
        CAST(total_jobs AS INT) AS total_jobs,
        CAST(successful_jobs AS INT) AS successful_jobs,
        CAST(failed_jobs AS INT) AS failed_jobs,
        CAST(total_records_loaded AS BIGINT) AS total_records_loaded,
        CAST(total_records_failed AS BIGINT) AS total_records_failed,
        avg_duration_seconds,
        CAST(last_run_timestamp AS STRING) AS last_run_timestamp
    FROM {catalog}.nemweb.ingestion_summary
    WHERE ingestion_date >= CURRENT_DATE() - INTERVAL {days} DAYS
    ORDER BY ingestion_date DESC, data_type, region_id
    """

    rows = await execute_sql(sql)

    return APIResponse(data=rows)


# ============================================================================
# Data Quality Endpoints
# ============================================================================

@router.post("/quality/run-checks")
async def run_quality_checks(
    region_id: str = Query(default='NSW1'),
    date: Optional[str] = Query(default=None),
) -> APIResponse[List[Dict[str, Any]]]:
    """
    Run data quality checks

    Args:
        region_id: Region to check
        date: Date to check (YYYY-MM-DD, default: today)

    Returns:
        List of quality check results
    """
    validator = get_quality_validator()

    check_date = datetime.fromisoformat(date) if date else datetime.now()

    results = await validator.run_all_checks(check_date, region_id)

    return APIResponse(data=results)


@router.get("/quality/metrics", response_model=APIResponse[List[QualityMetricInfo]])
async def get_quality_metrics(
    data_type: Optional[str] = Query(default=None),
    region_id: Optional[str] = Query(default=None),
    metric_name: Optional[str] = Query(default=None),
    days: int = Query(default=7, ge=1, le=90),
    limit: int = Query(default=100, ge=1, le=500),
) -> APIResponse[List[QualityMetricInfo]]:
    """
    Get data quality metrics

    Args:
        data_type: Filter by data type
        region_id: Filter by region
        metric_name: Filter by metric (COMPLETENESS, TIMELINESS, ACCURACY, CONSISTENCY)
        days: Number of days
        limit: Number of metrics

    Returns:
        List of quality metrics
    """
    catalog = get_settings().apex_catalog

    filters = [f"check_timestamp >= CURRENT_TIMESTAMP() - INTERVAL {days} DAYS"]
    if data_type:
        filters.append(f"data_type = '{data_type}'")
    if region_id:
        filters.append(f"region_id = '{region_id}'")
    if metric_name:
        filters.append(f"metric_name = '{metric_name}'")

    where_clause = f"WHERE {' AND '.join(filters)}"

    sql = f"""
    SELECT
        metric_id,
        CAST(check_timestamp AS STRING) AS check_timestamp,
        data_type,
        region_id,
        CAST(date_checked AS STRING) AS date_checked,
        metric_name,
        metric_value,
        threshold_value,
        passed,
        details
    FROM {catalog}.nemweb.data_quality_metrics
    {where_clause}
    ORDER BY check_timestamp DESC
    LIMIT {limit}
    """

    rows = await execute_sql(sql)
    metrics = [QualityMetricInfo.model_validate(r) for r in rows]

    return APIResponse(data=metrics)


@router.get("/quality/summary")
async def get_quality_summary(
    days: int = Query(default=7, ge=1, le=90),
) -> APIResponse[Dict[str, Any]]:
    """
    Get quality summary statistics

    Args:
        days: Number of days

    Returns:
        Quality summary
    """
    catalog = get_settings().apex_catalog

    sql = f"""
    SELECT
        data_type,
        metric_name,
        COUNT(*) AS total_checks,
        SUM(CASE WHEN passed THEN 1 ELSE 0 END) AS passed_checks,
        SUM(CASE WHEN NOT passed THEN 1 ELSE 0 END) AS failed_checks,
        AVG(metric_value) AS avg_metric_value,
        MIN(metric_value) AS min_metric_value,
        MAX(metric_value) AS max_metric_value
    FROM {catalog}.nemweb.data_quality_metrics
    WHERE check_timestamp >= CURRENT_TIMESTAMP() - INTERVAL {days} DAYS
    GROUP BY data_type, metric_name
    ORDER BY data_type, metric_name
    """

    rows = await execute_sql(sql)

    return APIResponse(data=rows)


# ============================================================================
# Statistics Endpoints
# ============================================================================

@router.get("/stats/daily-prices")
async def get_daily_price_stats(
    region_id: str = Query(default='NSW1'),
    days: int = Query(default=30, ge=1, le=365),
) -> APIResponse[List[Dict[str, Any]]]:
    """
    Get daily price statistics

    Args:
        region_id: Region ID
        days: Number of days

    Returns:
        Daily price stats
    """
    catalog = get_settings().apex_catalog

    sql = f"""
    SELECT
        CAST(price_date AS STRING) AS price_date,
        region_id,
        CAST(interval_count AS INT) AS interval_count,
        avg_price,
        min_price,
        max_price,
        price_volatility,
        median_price,
        p95_price,
        avg_demand_mw,
        peak_demand_mw,
        CAST(high_price_intervals AS INT) AS high_price_intervals,
        data_source
    FROM {catalog}.market_nem.daily_price_stats
    WHERE region_id = '{region_id}'
      AND price_date >= CURRENT_DATE() - INTERVAL {days} DAYS
    ORDER BY price_date DESC
    """

    rows = await execute_sql(sql)

    return APIResponse(data=rows)


@router.get("/stats/forecast-accuracy")
async def get_forecast_accuracy(
    region_id: str = Query(default='NSW1'),
    days: int = Query(default=30, ge=1, le=90),
) -> APIResponse[List[Dict[str, Any]]]:
    """
    Get forecast accuracy statistics

    Args:
        region_id: Region ID
        days: Number of days

    Returns:
        Forecast accuracy stats
    """
    catalog = get_settings().apex_catalog

    sql = f"""
    SELECT
        CAST(forecast_date AS STRING) AS forecast_date,
        region_id,
        CAST(interval_count AS INT) AS interval_count,
        avg_forecast_price,
        avg_actual_price,
        mae,
        mape,
        rmse,
        correlation
    FROM {catalog}.market_nem.forecast_accuracy
    WHERE region_id = '{region_id}'
      AND forecast_date >= CURRENT_DATE() - INTERVAL {days} DAYS
    ORDER BY forecast_date DESC
    """

    rows = await execute_sql(sql)

    return APIResponse(data=rows)
