from datetime import date, datetime
import logging
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.backend.database import execute_sql
from app.backend.models import APIResponse
from app.backend.sql_loader import load_sql

router = APIRouter(prefix='/api/v1/europe', tags=['europe'])
logger = logging.getLogger(__name__)


class EPEXPrice(BaseModel):
    bidding_zone: str
    delivery_datetime: datetime
    price_eur_mwh: float
    volume_mwh: float
    mtu_minutes: int
    is_negative: bool


class GenerationMixItem(BaseModel):
    fuel_type: str
    generation_mw: float
    pct_of_total: float


class SparkSpreadPoint(BaseModel):
    calculation_datetime: datetime
    power_price: float
    gas_price_mmbtu: float
    ets_price: float
    spark_spread: float
    clean_spark_spread: float


class GenerationAsset(BaseModel):
    asset_id: str
    asset_name: str
    operator: str
    country: str
    fuel_type: str
    capacity_mw: float
    openlink_incumbent: bool


class CrossBorderFlow(BaseModel):
    from_zone: str
    to_zone: str
    flow_mw: float
    atc_mw: float
    utilisation_pct: float
    is_constrained: bool


class AuditRecord(BaseModel):
    delivery_datetime: datetime
    bidding_zone: str
    price_eur_mwh: float
    data_source: str
    recorded_at: datetime


def _safe_sql(sql: str, **params: object) -> str:
    out = sql
    for k, v in params.items():
        if v is None:
            out = out.replace(f':{k}', 'NULL')
        elif isinstance(v, str):
            out = out.replace(f':{k}', f"'{v}'")
        else:
            out = out.replace(f':{k}', str(v))
    return out


@router.get('/prices/current', response_model=APIResponse[list[EPEXPrice]])
async def prices_current() -> APIResponse[list[EPEXPrice]]:
    sql = load_sql('data/queries/europe/epex_current_prices.sql')
    try:
        rows = await execute_sql(sql)
    except Exception as exc:
        logger.exception('Europe current prices SQL failed')
        raise HTTPException(status_code=503, detail=f'Europe current prices query failed: {exc}') from exc
    out = [EPEXPrice.model_validate({'bidding_zone': r.get('bidding_zone'), 'delivery_datetime': r.get('delivery_datetime'), 'price_eur_mwh': float(r.get('price_eur_mwh', 0)), 'volume_mwh': float(r.get('volume_mwh', 0)), 'mtu_minutes': int(r.get('market_time_unit_minutes', r.get('mtu_minutes', 60))), 'is_negative': float(r.get('price_eur_mwh', 0)) < 0}) for r in rows]
    return APIResponse(data=out, region='EUR')


@router.get('/prices/history', response_model=APIResponse[list[EPEXPrice]])
async def prices_history(bidding_zone: str | None = None, hours: int = Query(default=24, ge=1, le=720)) -> APIResponse[list[EPEXPrice]]:
    sql = _safe_sql(load_sql('data/queries/europe/epex_price_history.sql'), bidding_zone=bidding_zone or 'NULL', hours=hours)
    try:
        rows = await execute_sql(sql)
    except Exception as exc:
        logger.exception('Europe price history SQL failed')
        raise HTTPException(status_code=503, detail=f'Europe price history query failed: {exc}') from exc
    out = [EPEXPrice.model_validate({'bidding_zone': r.get('bidding_zone'), 'delivery_datetime': r.get('delivery_datetime'), 'price_eur_mwh': float(r.get('price_eur_mwh', 0)), 'volume_mwh': float(r.get('volume_mwh', 0)), 'mtu_minutes': int(r.get('market_time_unit_minutes', r.get('mtu_minutes', 60))), 'is_negative': float(r.get('price_eur_mwh', 0)) < 0}) for r in rows]
    return APIResponse(data=out, region='EUR')


@router.get('/generation/mix', response_model=APIResponse[list[GenerationMixItem]])
async def generation_mix(bidding_zone: str = 'DE-LU') -> APIResponse[list[GenerationMixItem]]:
    sql = _safe_sql(load_sql('data/queries/europe/generation_mix.sql'), bidding_zone=bidding_zone)
    try:
        rows = await execute_sql(sql)
    except Exception as exc:
        logger.exception('Europe generation mix SQL failed')
        raise HTTPException(status_code=503, detail=f'Europe generation mix query failed: {exc}') from exc
    total = sum(float(r.get('generation_mw', 0)) for r in rows) or 1.0
    out = [GenerationMixItem(fuel_type=str(r.get('fuel_type')), generation_mw=float(r.get('generation_mw', 0)), pct_of_total=round(float(r.get('generation_mw', 0)) / total * 100, 2)) for r in rows]
    return APIResponse(data=out, region='EUR')


@router.get('/spreads/spark', response_model=APIResponse[list[SparkSpreadPoint]])
async def spark_spreads(bidding_zone: str = 'DE-LU') -> APIResponse[list[SparkSpreadPoint]]:
    sql = _safe_sql(load_sql('data/queries/europe/spark_spread_history.sql'), bidding_zone=bidding_zone)
    try:
        rows = await execute_sql(sql)
    except Exception as exc:
        logger.exception('Europe spark spreads SQL failed')
        raise HTTPException(status_code=503, detail=f'Europe spark spreads query failed: {exc}') from exc
    return APIResponse(data=[SparkSpreadPoint.model_validate(r) for r in rows], region='EUR')


@router.get('/assets/openlink-incumbent', response_model=APIResponse[list[GenerationAsset]])
async def openlink_assets() -> APIResponse[list[GenerationAsset]]:
    sql = load_sql('data/queries/europe/openlink_displacement_summary.sql')
    try:
        rows = await execute_sql(sql)
    except Exception as exc:
        logger.exception('Europe openlink assets SQL failed')
        raise HTTPException(status_code=503, detail=f'Europe openlink assets query failed: {exc}') from exc
    return APIResponse(data=[GenerationAsset.model_validate(r) for r in rows], region='EUR')


@router.get('/flows/cross-border', response_model=APIResponse[list[CrossBorderFlow]])
async def cross_border() -> APIResponse[list[CrossBorderFlow]]:
    sql = load_sql('data/queries/europe/cross_border_utilisation.sql')
    try:
        rows = await execute_sql(sql)
    except Exception as exc:
        logger.exception('Europe cross-border flow SQL failed')
        raise HTTPException(status_code=503, detail=f'Europe cross-border flow query failed: {exc}') from exc
    out = [CrossBorderFlow(from_zone=str(r.get('from_zone')), to_zone=str(r.get('to_zone')), flow_mw=float(r.get('flow_mw', 0)), atc_mw=float(r.get('atc_mw', 0)), utilisation_pct=float(r.get('utilisation_pct', 0)), is_constrained=float(r.get('utilisation_pct', 0)) > 90) for r in rows]
    return APIResponse(data=out, region='EUR')


@router.get('/audit/remit', response_model=APIResponse[list[AuditRecord]])
async def remit_audit(bidding_zone: str = 'DE-LU', audit_date: date | None = None) -> APIResponse[list[AuditRecord]]:
    date_val = audit_date.isoformat() if audit_date else datetime.utcnow().date().isoformat()
    sql = _safe_sql(load_sql('data/queries/europe/remit_audit_example.sql'), bidding_zone=bidding_zone, audit_date=date_val)
    try:
        rows = await execute_sql(sql)
    except Exception as exc:
        logger.exception('Europe REMIT audit SQL failed')
        raise HTTPException(status_code=503, detail=f'Europe REMIT audit query failed: {exc}') from exc
    out = [AuditRecord(delivery_datetime=r.get('delivery_datetime'), bidding_zone=str(r.get('bidding_zone')), price_eur_mwh=float(r.get('price_eur_mwh', 0)), data_source=str(r.get('data_source', 'SIMULATED')), recorded_at=r.get('recorded_at') or r.get('delivery_datetime')) for r in rows]
    return APIResponse(data=out, region='EUR')
