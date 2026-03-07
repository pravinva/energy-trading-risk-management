from datetime import date
import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.backend.database import execute_sql
from app.backend.models import APIResponse
from app.backend.sql_loader import load_sql

router = APIRouter(prefix='/api/v1/americas', tags=['americas'])
logger = logging.getLogger(__name__)


class ISOPrice(BaseModel):
    iso_id: str
    node_id: str
    node_name: str
    zone: str
    lmp: float
    energy_component: float
    congestion_component: float
    loss_component: float
    interval_datetime: object


class RTCBComparison(BaseModel):
    period: str
    avg_tb4_spread: float
    avg_drrs_mw: float
    avg_output_mw: float
    avg_soc_pct: float
    record_count: int


class CapacityAuction(BaseModel):
    delivery_year: str
    clearing_price_mw_day: float
    total_cost_billions: float
    data_center_cost_pct: float
    price_cap_hit: bool
    reliability_shortfall_mw: float
    capacity_cost_per_mw_per_year: float


class NodalBasisNode(BaseModel):
    node_id: str
    node_name: str
    avg_basis_spread: float
    max_basis_spread: float
    pct_hours_positive: float


class CrossISOSpread(BaseModel):
    date: date
    pjm_aep_hub_price: float
    ercot_houston_price: float
    spread: float
    spread_direction: str


class LMPHistoryPoint(BaseModel):
    iso_id: str
    interval_datetime: object
    lmp: float
    energy_component: float
    congestion_component: float
    loss_component: float


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


@router.get('/prices/current', response_model=APIResponse[list[ISOPrice]])
async def prices_current(iso_id: str | None = None) -> APIResponse[list[ISOPrice]]:
    sql = _safe_sql(load_sql('data/queries/americas/multi_iso_lmp_current.sql'), iso_id=iso_id)
    try:
        rows = await execute_sql(sql)
    except Exception as exc:
        logger.exception('Americas current prices SQL failed')
        raise HTTPException(status_code=503, detail=f'Americas current prices query failed: {exc}') from exc
    return APIResponse(data=[ISOPrice.model_validate(r) for r in rows], region='AMER')


@router.get('/prices/history', response_model=APIResponse[list[LMPHistoryPoint]])
async def prices_history(iso_id: str = 'ERCOT', hours: int = 24) -> APIResponse[list[LMPHistoryPoint]]:
    sql = _safe_sql(load_sql('data/queries/americas/multi_iso_lmp_history.sql'), iso_id=iso_id, hours=hours)
    try:
        rows = await execute_sql(sql)
    except Exception as exc:
        logger.exception('Americas price history SQL failed')
        raise HTTPException(status_code=503, detail=f'Americas price history query failed: {exc}') from exc
    return APIResponse(data=[LMPHistoryPoint.model_validate(r) for r in rows], region='AMER')


@router.get('/ercot/rtcb-comparison/{resource_id}', response_model=APIResponse[list[RTCBComparison]])
async def rtcb(resource_id: str) -> APIResponse[list[RTCBComparison]]:
    sql = _safe_sql(load_sql('data/queries/americas/ercot_rtcb_comparison.sql'), resource_id=resource_id)
    try:
        rows = await execute_sql(sql)
    except Exception as exc:
        logger.exception('Americas ERCOT RTC+B SQL failed')
        raise HTTPException(status_code=503, detail=f'Americas RTC+B query failed: {exc}') from exc
    mapped = []
    for r in rows:
        mapped.append(RTCBComparison(period=str(r.get('period')), avg_tb4_spread=float(r.get('avg_tb4_spread', 0)), avg_drrs_mw=float(r.get('avg_drrs_mw', 0)), avg_output_mw=float(r.get('avg_output_mw', 0)), avg_soc_pct=float(r.get('avg_soc_pct', 0)), record_count=int(r.get('total_count', r.get('record_count', 0)))))
    return APIResponse(data=mapped, region='AMER')


@router.get('/pjm/capacity-auctions', response_model=APIResponse[list[CapacityAuction]])
async def pjm() -> APIResponse[list[CapacityAuction]]:
    sql = load_sql('data/queries/americas/pjm_capacity_auction_history.sql')
    try:
        rows = await execute_sql(sql)
    except Exception as exc:
        logger.exception('Americas PJM capacity SQL failed')
        raise HTTPException(status_code=503, detail=f'Americas PJM capacity query failed: {exc}') from exc
    return APIResponse(data=[CapacityAuction.model_validate(r) for r in rows], region='AMER')


@router.get('/ieso/nodal-basis', response_model=APIResponse[list[NodalBasisNode]])
async def ieso() -> APIResponse[list[NodalBasisNode]]:
    sql = load_sql('data/queries/americas/ieso_nodal_basis_leaders.sql')
    try:
        rows = await execute_sql(sql)
    except Exception as exc:
        logger.exception('Americas IESO nodal basis SQL failed')
        raise HTTPException(status_code=503, detail=f'Americas IESO nodal basis query failed: {exc}') from exc
    out = [NodalBasisNode(node_id=str(r.get('node_id')), node_name=str(r.get('node_name', r.get('node_id'))), avg_basis_spread=float(r.get('avg_basis_spread', 0)), max_basis_spread=float(r.get('max_basis_spread', 0)), pct_hours_positive=float(r.get('pct_hours_positive_basis', r.get('pct_hours_positive', 0)))) for r in rows]
    return APIResponse(data=out, region='AMER')


@router.get('/intelligence/data-center-lmp', response_model=APIResponse[list[dict]])
async def data_center(iso_id: str = 'PJM') -> APIResponse[list[dict]]:
    sql = _safe_sql(load_sql('data/queries/americas/data_center_lmp_correlation.sql'), iso_id=iso_id)
    try:
        rows = await execute_sql(sql)
    except Exception as exc:
        logger.exception('Americas data center intelligence SQL failed')
        raise HTTPException(status_code=503, detail=f'Americas data center intelligence query failed: {exc}') from exc
    return APIResponse(data=rows, region='AMER')


@router.get('/intelligence/cross-iso-spread', response_model=APIResponse[list[CrossISOSpread]])
async def spread() -> APIResponse[list[CrossISOSpread]]:
    sql = load_sql('data/queries/americas/cross_iso_spread.sql')
    try:
        rows = await execute_sql(sql)
    except Exception as exc:
        logger.exception('Americas cross-ISO spread SQL failed')
        raise HTTPException(status_code=503, detail=f'Americas cross-ISO spread query failed: {exc}') from exc
    out = []
    for r in rows:
        sp = float(r.get('spread', 0))
        out.append(CrossISOSpread(date=r.get('date'), pjm_aep_hub_price=float(r.get('pjm_aep_hub_price', 0)), ercot_houston_price=float(r.get('ercot_houston_price', 0)), spread=sp, spread_direction='PJM_PREMIUM' if sp > 0.5 else 'ERCOT_PREMIUM' if sp < -0.5 else 'FLAT'))
    return APIResponse(data=out, region='AMER')
