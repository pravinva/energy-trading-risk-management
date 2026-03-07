from datetime import date, datetime
import logging
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.backend.database import execute_sql
from app.backend.models import APIResponse
from app.backend.sql_loader import load_sql

router = APIRouter(prefix='/api/v1/anz', tags=['anz'])
logger = logging.getLogger(__name__)


class DispatchInterval(BaseModel):
    interval_datetime: datetime
    region_id: str
    rrp: float
    totaldemand: float
    raise5min: float
    lower5min: float
    raisereg: float
    lowerreg: float


class RegionCurrentPrice(BaseModel):
    region_id: str
    rrp: float
    change_vs_prev: float
    pct_change: float
    is_spike: bool


class BESSAsset(BaseModel):
    duid: str
    asset_name: str
    operator: str
    region_id: str
    capacity_mw: float
    duration_hours: float
    current_soc_pct: float
    current_output_mw: float
    today_revenue: float
    annual_revenue_ytd: float


class BESSFleetSummary(BaseModel):
    assets: list[BESSAsset]
    total_fleet_mw: float
    total_fleet_charging_mw: float
    total_fleet_discharging_mw: float
    fleet_fcas_mw: float


class TelemetryPoint(BaseModel):
    recorded_at: datetime
    state_of_charge_pct: float
    output_mw: float
    fcas_raise_mw: float
    fcas_lower_mw: float


class RevenueDay(BaseModel):
    settlement_date: date
    energy_revenue: float
    fcas_total_revenue: float
    total_revenue: float


class FCASMarketState(BaseModel):
    region_id: str
    lower6sec_avg: float
    raise6sec_avg: float
    lowerreg_avg: float
    raisereg_avg: float


class SpikeEvent(BaseModel):
    start_datetime: datetime
    end_datetime: datetime
    region_id: str
    peak_rrp: float
    duration_minutes: int


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


@router.get('/prices/current', response_model=APIResponse[list[RegionCurrentPrice]])
async def prices_current() -> APIResponse[list[RegionCurrentPrice]]:
    sql = load_sql('data/queries/anz/rrp_current.sql')
    try:
        rows = await execute_sql(sql)
    except Exception as exc:
        logger.exception('ANZ current prices SQL failed')
        raise HTTPException(status_code=503, detail=f'ANZ current prices query failed: {exc}') from exc
    parsed = [RegionCurrentPrice.model_validate(r) for r in rows]
    return APIResponse(data=parsed, region='ANZ')


@router.get('/prices/history', response_model=APIResponse[list[DispatchInterval]])
async def prices_history(hours: int = Query(default=24, ge=1, le=168), region_id: str | None = None) -> APIResponse[list[DispatchInterval]]:
    sql = _safe_sql(load_sql('data/queries/anz/rrp_by_region.sql'), hours=hours, region_id=region_id)
    try:
        rows = await execute_sql(sql)
    except Exception as exc:
        logger.exception('ANZ price history SQL failed')
        raise HTTPException(status_code=503, detail=f'ANZ price history query failed: {exc}') from exc
    return APIResponse(data=[DispatchInterval.model_validate(r) for r in rows], region='ANZ')


@router.get('/bess/fleet', response_model=APIResponse[BESSFleetSummary])
async def bess_fleet() -> APIResponse[BESSFleetSummary]:
    try:
        rows = await execute_sql(load_sql('data/queries/anz/bess_fleet_summary.sql'))
    except Exception as exc:
        logger.exception('ANZ BESS fleet SQL failed')
        raise HTTPException(status_code=503, detail=f'ANZ BESS fleet query failed: {exc}') from exc
    assets = [BESSAsset.model_validate(r) for r in rows]
    try:
        fcas_rows = await execute_sql(
            """
            WITH latest AS (
              SELECT duid, fcas_raise_mw, fcas_lower_mw,
                     ROW_NUMBER() OVER (PARTITION BY duid ORDER BY recorded_at DESC) AS rn
              FROM serverless_sandbox_tladem_catalog.nexus_anz.bess_telemetry
            )
            SELECT COALESCE(SUM((fcas_raise_mw + fcas_lower_mw) / 2.0), 0) AS fleet_fcas_mw
            FROM latest WHERE rn = 1
            """
        )
    except Exception as exc:
        logger.exception('ANZ fleet FCAS aggregation SQL failed')
        raise HTTPException(status_code=503, detail=f'ANZ fleet FCAS query failed: {exc}') from exc
    fleet_fcas = float(fcas_rows[0].get("fleet_fcas_mw", 0)) if fcas_rows else 0.0
    return APIResponse(
        data=BESSFleetSummary(
            assets=assets,
            total_fleet_mw=sum(a.capacity_mw for a in assets),
            total_fleet_charging_mw=sum(abs(a.current_output_mw) for a in assets if a.current_output_mw < 0),
            total_fleet_discharging_mw=sum(a.current_output_mw for a in assets if a.current_output_mw > 0),
            fleet_fcas_mw=round(fleet_fcas, 2),
        ),
        region='ANZ',
    )


@router.get('/bess/{duid}/telemetry', response_model=APIResponse[list[TelemetryPoint]])
async def bess_telemetry(duid: str, hours: int = Query(default=24, ge=1, le=168)) -> APIResponse[list[TelemetryPoint]]:
    sql = _safe_sql(load_sql('data/queries/anz/bess_telemetry_timeseries.sql'), duid=duid, hours=hours)
    try:
        rows = await execute_sql(sql)
    except Exception as exc:
        logger.exception('ANZ telemetry SQL failed')
        raise HTTPException(status_code=503, detail=f'ANZ telemetry query failed: {exc}') from exc
    return APIResponse(data=[TelemetryPoint.model_validate(r) for r in rows], region='ANZ')


@router.get('/bess/{duid}/revenue', response_model=APIResponse[list[RevenueDay]])
async def bess_revenue(duid: str, days: int = Query(default=30, ge=1, le=365)) -> APIResponse[list[RevenueDay]]:
    sql = _safe_sql(load_sql('data/queries/anz/revenue_attribution.sql'), duid=duid, days=days)
    try:
        rows = await execute_sql(sql)
    except Exception as exc:
        logger.exception('ANZ revenue SQL failed')
        raise HTTPException(status_code=503, detail=f'ANZ revenue query failed: {exc}') from exc
    mapped = []
    for r in rows:
        energy = float(r.get('energy_revenue', 0))
        fcas = float(r.get('fcas_total_revenue', r.get('fcas_raise5min_revenue', 0)))
        mapped.append(RevenueDay(settlement_date=r.get('settlement_date'), energy_revenue=energy, fcas_total_revenue=fcas, total_revenue=float(r.get('total_revenue', energy + fcas))))
    return APIResponse(data=mapped, region='ANZ')


@router.get('/fcas/summary', response_model=APIResponse[list[FCASMarketState]])
async def fcas_summary() -> APIResponse[list[FCASMarketState]]:
    sql = load_sql('data/queries/anz/fcas_market_summary.sql')
    try:
        rows = await execute_sql(sql)
    except Exception as exc:
        logger.exception('ANZ FCAS summary SQL failed')
        raise HTTPException(status_code=503, detail=f'ANZ FCAS summary query failed: {exc}') from exc
    return APIResponse(data=[FCASMarketState.model_validate(r) for r in rows], region='ANZ')


@router.get('/spikes', response_model=APIResponse[list[SpikeEvent]])
async def spikes(days: int = Query(default=90, ge=1, le=365)) -> APIResponse[list[SpikeEvent]]:
    sql = load_sql('data/queries/anz/spike_events.sql').replace("interval 90 days", f"interval {days} days")
    try:
        rows = await execute_sql(sql)
    except Exception as exc:
        logger.exception('ANZ spikes SQL failed')
        raise HTTPException(status_code=503, detail=f'ANZ spikes query failed: {exc}') from exc
    return APIResponse(data=[SpikeEvent.model_validate(r) for r in rows], region='ANZ')
