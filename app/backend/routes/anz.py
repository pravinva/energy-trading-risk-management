from datetime import date, datetime
import logging
from fastapi import APIRouter, Query
from pydantic import BaseModel

from app.backend.data_store import anz_fcas_summary, anz_fleet, anz_price_history, anz_prices_current, anz_revenue, anz_spikes, anz_telemetry
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
        parsed = []
        for r in rows:
            rrp = float(r.get('rrp', 0))
            parsed.append(RegionCurrentPrice(region_id=str(r.get('region_id', 'NA')), rrp=rrp, change_vs_prev=0.0, pct_change=0.0, is_spike=rrp > 1000))
        return APIResponse(data=parsed, region='ANZ')
    except Exception:
        return APIResponse(data=[RegionCurrentPrice.model_validate(r) for r in anz_prices_current()], region='ANZ')


@router.get('/prices/history', response_model=APIResponse[list[DispatchInterval]])
async def prices_history(hours: int = Query(default=24, ge=1, le=168), region_id: str | None = None) -> APIResponse[list[DispatchInterval]]:
    sql = _safe_sql(load_sql('data/queries/anz/rrp_by_region.sql'), hours=hours, region_id=region_id)
    try:
        rows = await execute_sql(sql)
        if rows:
            return APIResponse(data=[DispatchInterval.model_validate(r) for r in rows], region='ANZ')
    except Exception as exc:
        logger.warning('Falling back to in-memory ANZ history data: %s', exc)
    return APIResponse(data=[DispatchInterval.model_validate(r) for r in anz_price_history(hours=hours, region_id=region_id)], region='ANZ')


@router.get('/bess/fleet', response_model=APIResponse[BESSFleetSummary])
async def bess_fleet() -> APIResponse[BESSFleetSummary]:
    assets = [BESSAsset.model_validate(r) for r in anz_fleet()]
    return APIResponse(
        data=BESSFleetSummary(
            assets=assets,
            total_fleet_mw=sum(a.capacity_mw for a in assets),
            total_fleet_charging_mw=sum(abs(a.current_output_mw) for a in assets if a.current_output_mw < 0),
            total_fleet_discharging_mw=sum(a.current_output_mw for a in assets if a.current_output_mw > 0),
            fleet_fcas_mw=sum(a.capacity_mw * 0.1 for a in assets),
        ),
        region='ANZ',
    )


@router.get('/bess/{duid}/telemetry', response_model=APIResponse[list[TelemetryPoint]])
async def bess_telemetry(duid: str, hours: int = Query(default=24, ge=1, le=168)) -> APIResponse[list[TelemetryPoint]]:
    sql = _safe_sql(load_sql('data/queries/anz/bess_telemetry_timeseries.sql'), duid=duid, hours=hours)
    try:
        rows = await execute_sql(sql)
        if rows:
            return APIResponse(data=[TelemetryPoint.model_validate(r) for r in rows], region='ANZ')
    except Exception as exc:
        logger.warning('Falling back to in-memory ANZ telemetry data: %s', exc)
    return APIResponse(data=[TelemetryPoint.model_validate(r) for r in anz_telemetry(duid=duid, hours=hours)], region='ANZ')


@router.get('/bess/{duid}/revenue', response_model=APIResponse[list[RevenueDay]])
async def bess_revenue(duid: str, days: int = Query(default=30, ge=1, le=365)) -> APIResponse[list[RevenueDay]]:
    sql = _safe_sql(load_sql('data/queries/anz/revenue_attribution.sql'), duid=duid, days=days)
    try:
        rows = await execute_sql(sql)
        if rows:
            mapped = []
            for r in rows:
                energy = float(r.get('energy_revenue', 0))
                fcas = float(r.get('fcas_total_revenue', r.get('fcas_raise5min_revenue', 0)))
                mapped.append(RevenueDay(settlement_date=r.get('settlement_date'), energy_revenue=energy, fcas_total_revenue=fcas, total_revenue=float(r.get('total_revenue', energy + fcas))))
            return APIResponse(data=mapped, region='ANZ')
    except Exception as exc:
        logger.warning('Falling back to in-memory ANZ revenue data: %s', exc)
    return APIResponse(data=[RevenueDay.model_validate(r) for r in anz_revenue(duid=duid, days=days)], region='ANZ')


@router.get('/fcas/summary', response_model=APIResponse[list[FCASMarketState]])
async def fcas_summary() -> APIResponse[list[FCASMarketState]]:
    sql = load_sql('data/queries/anz/fcas_market_summary.sql')
    try:
        rows = await execute_sql(sql)
        if rows:
            return APIResponse(data=[FCASMarketState.model_validate(r) for r in rows], region='ANZ')
    except Exception as exc:
        logger.warning('Falling back to in-memory ANZ FCAS data: %s', exc)
    return APIResponse(data=[FCASMarketState.model_validate(r) for r in anz_fcas_summary()], region='ANZ')


@router.get('/spikes', response_model=APIResponse[list[SpikeEvent]])
async def spikes(days: int = Query(default=90, ge=1, le=365)) -> APIResponse[list[SpikeEvent]]:
    _ = load_sql('data/queries/anz/spike_events.sql')
    return APIResponse(data=[SpikeEvent.model_validate(r) for r in anz_spikes(days=days)], region='ANZ')
