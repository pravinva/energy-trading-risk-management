from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.backend.config import get_settings
from app.backend.database import execute_sql
from app.backend.models import APIResponse

router = APIRouter(prefix="/api/v1/portfolio", tags=["portfolio"])


class RevenueComponent(BaseModel):
    component: str
    annual_value: float
    contribution_pct: float


class PPARow(BaseModel):
    ppa_id: str
    counterparty: str
    volume_mw: float
    strike_price: float
    tenor_years: int


class BenchmarkRow(BaseModel):
    rank: int
    asset: str
    rev_per_mw: float
    vs_benchmark_pct: float


class SimulationComponent(BaseModel):
    component: str
    annual_value: float
    contribution_pct: float


class SimulationDefaults(BaseModel):
    market: str
    duration_hours_default: int
    duration_hours_max: int
    ancillary_pct_default: int
    ancillary_pct_max: int
    ppa_mw_default: int
    ppa_mw_max: int
    ppa_mtm_factor: float


@router.get("/revenue-stacking", response_model=APIResponse[list[RevenueComponent]])
async def revenue_stacking(market: str = Query(default='NEM')) -> APIResponse[list[RevenueComponent]]:
    market_key = market.upper()
    catalog = get_settings().apex_catalog
    await execute_sql(
        f"CREATE TABLE IF NOT EXISTS {catalog}.portfolio.revenue_rates ("
        f"component STRING, rate_value DOUBLE)"
    )
    sql = (
        f"WITH base AS ("
        f"  SELECT "
        f"    ABS(SUM(price * volume_mw)) AS traded_notional, "
        f"    SUM(CASE WHEN upper(direction)='SELL' THEN price*volume_mw ELSE 0 END) AS sell_value, "
        f"    SUM(CASE WHEN upper(direction)='BUY' THEN price*volume_mw ELSE 0 END) AS buy_cost, "
        f"    SUM(ABS(volume_mw)) AS gross_mw "
        f"  FROM {catalog}.trading.trades WHERE upper(market)='{market_key}'"
        f"), rates AS ("
        f"  SELECT "
        f"    MAX(CASE WHEN component='Ancillary Services' THEN rate_value END) AS ancillary_rate, "
        f"    MAX(CASE WHEN component='Capacity Daily Rate' THEN rate_value END) AS capacity_daily_rate, "
        f"    MAX(CASE WHEN component='PPA Hedge Value' THEN rate_value END) AS ppa_rate "
        f"  FROM {catalog}.portfolio.revenue_rates"
        f"), comp AS ("
        f"  SELECT 'Energy Arbitrage' AS component, GREATEST(sell_value - buy_cost, 0) AS annual_value FROM base "
        f"  UNION ALL "
        f"  SELECT 'Ancillary Services' AS component, traded_notional * COALESCE(ancillary_rate, 0) AS annual_value FROM base CROSS JOIN rates "
        f"  UNION ALL "
        f"  SELECT 'Capacity' AS component, gross_mw * 365 * COALESCE(capacity_daily_rate, 0) AS annual_value FROM base CROSS JOIN rates "
        f"  UNION ALL "
        f"  SELECT 'PPA Hedge Value' AS component, traded_notional * COALESCE(ppa_rate, 0) AS annual_value FROM base CROSS JOIN rates"
        f") "
        f"SELECT component, annual_value, "
        f"CASE WHEN SUM(annual_value) OVER () = 0 THEN 0 ELSE annual_value / SUM(annual_value) OVER () * 100 END AS contribution_pct "
        f"FROM comp ORDER BY annual_value DESC"
    )
    rows = await execute_sql(sql)
    out = [
        RevenueComponent(
            component=str(r.get("component")),
            annual_value=float(r.get("annual_value", 0)),
            contribution_pct=float(r.get("contribution_pct", 0)),
        )
        for r in rows
    ]
    return APIResponse(data=out, region=market_key)


@router.get("/ppa-book", response_model=APIResponse[list[PPARow]])
async def ppa_book(market: str = Query(default='NEM')) -> APIResponse[list[PPARow]]:
    market_key = market.upper()
    catalog = get_settings().apex_catalog
    sql = (
        f"SELECT "
        f"CONCAT(upper(market), '-PPA-', LPAD(CAST(ROW_NUMBER() OVER (ORDER BY source_system, trader_id) AS STRING), 3, '0')) AS ppa_id, "
        f"COALESCE(source_system, 'UNKNOWN') AS counterparty, "
        f"ROUND(SUM(ABS(volume_mw)), 2) AS volume_mw, "
        f"ROUND(SUM(price * ABS(volume_mw)) / NULLIF(SUM(ABS(volume_mw)), 0), 2) AS strike_price, "
        f"CAST(GREATEST(1, LEAST(15, FLOOR(DATEDIFF(current_date(), DATE(MIN(ingested_at))) / 365) + 5)) AS INT) AS tenor_years "
        f"FROM {catalog}.trading.trades "
        f"WHERE upper(market)='{market_key}' "
        f"GROUP BY market, source_system, trader_id "
        f"ORDER BY volume_mw DESC LIMIT 12"
    )
    rows = await execute_sql(sql)
    out = [PPARow.model_validate(r) for r in rows]
    return APIResponse(data=out, region=market_key)


@router.get("/asset-benchmark", response_model=APIResponse[list[BenchmarkRow]])
async def asset_benchmark(market: str = Query(default='NEM')) -> APIResponse[list[BenchmarkRow]]:
    market_key = market.upper()
    catalog = get_settings().apex_catalog
    sql = (
        f"WITH ppa AS ("
        f"  SELECT "
        f"    COALESCE(source_system, 'UNKNOWN') AS asset, "
        f"    ROUND(SUM(ABS(volume_mw)), 4) AS mw, "
        f"    ROUND(SUM(price * ABS(volume_mw)) / NULLIF(SUM(ABS(volume_mw)), 0), 4) AS strike "
        f"  FROM {catalog}.trading.trades "
        f"  WHERE upper(market)='{market_key}' "
        f"  GROUP BY source_system"
        f"), scored AS ("
        f"  SELECT "
        f"    asset, "
        f"    CASE WHEN mw = 0 THEN 0 ELSE strike END AS rev_per_mw, "
        f"    AVG(CASE WHEN mw = 0 THEN 0 ELSE strike END) OVER () AS benchmark "
        f"  FROM ppa"
        f"), ranked AS ("
        f"  SELECT "
        f"    ROW_NUMBER() OVER (ORDER BY rev_per_mw DESC) AS rank, "
        f"    asset, "
        f"    rev_per_mw, "
        f"    CASE WHEN benchmark = 0 THEN 0 ELSE (rev_per_mw / benchmark - 1) * 100 END AS vs_benchmark_pct "
        f"  FROM scored"
        f") "
        f"SELECT rank, asset, rev_per_mw, vs_benchmark_pct FROM ranked ORDER BY rank"
    )
    rows = await execute_sql(sql)
    out = [BenchmarkRow.model_validate(r) for r in rows]
    return APIResponse(data=out, region=market_key)


@router.get("/simulation", response_model=APIResponse[list[SimulationComponent]])
async def simulation(
    market: str = Query(default='NEM'),
    duration_hours: int = Query(default=2, ge=1, le=8),
    ancillary_pct: int = Query(default=40, ge=0, le=100),
    ppa_mw: int = Query(default=50, ge=0, le=300),
) -> APIResponse[list[SimulationComponent]]:
    market_key = market.upper()
    catalog = get_settings().apex_catalog
    await execute_sql(
        f"CREATE TABLE IF NOT EXISTS {catalog}.portfolio.revenue_rates ("
        f"component STRING, rate_value DOUBLE)"
    )
    sql = (
        f"WITH base AS ("
        f"  SELECT "
        f"    ABS(SUM(price * volume_mw)) AS traded_notional, "
        f"    SUM(CASE WHEN upper(direction)='SELL' THEN price*volume_mw ELSE 0 END) AS sell_value, "
        f"    SUM(CASE WHEN upper(direction)='BUY' THEN price*volume_mw ELSE 0 END) AS buy_cost, "
        f"    SUM(ABS(volume_mw)) AS gross_mw "
        f"  FROM {catalog}.trading.trades WHERE upper(market)='{market_key}'"
        f"), rates AS ("
        f"  SELECT "
        f"    MAX(CASE WHEN component='Ancillary Services' THEN rate_value END) AS ancillary_rate, "
        f"    MAX(CASE WHEN component='Capacity Daily Rate' THEN rate_value END) AS capacity_daily_rate, "
        f"    MAX(CASE WHEN component='PPA Hedge Value' THEN rate_value END) AS ppa_rate "
        f"  FROM {catalog}.portfolio.revenue_rates"
        f"), comp AS ("
        f"  SELECT 'Energy Arbitrage' AS component, "
        f"    GREATEST(sell_value - buy_cost, 0) * ({duration_hours} / 2.0) AS annual_value "
        f"  FROM base "
        f"  UNION ALL "
        f"  SELECT 'Ancillary Services' AS component, "
        f"    traded_notional * COALESCE(ancillary_rate, 0) * ({ancillary_pct} / 40.0) AS annual_value "
        f"  FROM base CROSS JOIN rates "
        f"  UNION ALL "
        f"  SELECT 'Capacity' AS component, "
        f"    gross_mw * 365 * COALESCE(capacity_daily_rate, 0) * (1 + ({ppa_mw} / 600.0)) AS annual_value "
        f"  FROM base CROSS JOIN rates "
        f"  UNION ALL "
        f"  SELECT 'PPA Hedge Value' AS component, "
        f"    traded_notional * COALESCE(ppa_rate, 0) * (1 + ({ppa_mw} / 200.0)) AS annual_value "
        f"  FROM base CROSS JOIN rates"
        f") "
        f"SELECT component, ROUND(annual_value, 2) AS annual_value, "
        f"  CASE WHEN SUM(annual_value) OVER () = 0 THEN 0 ELSE ROUND(annual_value / SUM(annual_value) OVER () * 100, 2) END AS contribution_pct "
        f"FROM comp ORDER BY annual_value DESC"
    )
    rows = await execute_sql(sql)
    out = [SimulationComponent.model_validate(r) for r in rows]
    return APIResponse(data=out, region=market_key)


@router.get("/simulation-defaults", response_model=APIResponse[SimulationDefaults])
async def simulation_defaults(market: str = Query(default='NEM')) -> APIResponse[SimulationDefaults]:
    market_key = market.upper()
    catalog = get_settings().apex_catalog
    await execute_sql(
        f"CREATE TABLE IF NOT EXISTS {catalog}.portfolio.simulation_defaults ("
        f"market STRING, duration_hours_default INT, duration_hours_max INT, "
        f"ancillary_pct_default INT, ancillary_pct_max INT, ppa_mw_default INT, ppa_mw_max INT, ppa_mtm_factor DOUBLE)"
    )
    rows = await execute_sql(
        f"SELECT market, duration_hours_default, duration_hours_max, ancillary_pct_default, ancillary_pct_max, "
        f"ppa_mw_default, ppa_mw_max, ppa_mtm_factor "
        f"FROM {catalog}.portfolio.simulation_defaults WHERE upper(market)='{market_key}' LIMIT 1"
    )
    if not rows:
        rows = await execute_sql(
            f"SELECT market, duration_hours_default, duration_hours_max, ancillary_pct_default, ancillary_pct_max, "
            f"ppa_mw_default, ppa_mw_max, ppa_mtm_factor "
            f"FROM {catalog}.portfolio.simulation_defaults WHERE upper(market)='NEM' LIMIT 1"
        )
    if not rows:
        raise HTTPException(status_code=404, detail=f"No simulation defaults configured for market {market_key}")
    return APIResponse(data=SimulationDefaults.model_validate(rows[0]), region=market_key)
