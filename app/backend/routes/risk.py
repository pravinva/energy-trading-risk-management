from __future__ import annotations

from datetime import datetime, timezone
from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

from app.backend.config import get_settings
from app.backend.database import execute_sql
from app.backend.models import APIResponse

router = APIRouter(prefix="/api/v1/risk", tags=["risk"])


class VaRRequest(BaseModel):
    confidence: float = Field(default=0.95, ge=0.9, le=0.99)
    volatility: float = Field(default=0.12, gt=0)
    spot_price: float = Field(default=96.0, gt=0)


class VaRResponse(BaseModel):
    exposure_mw: float
    var_95: float
    var_99: float
    expected_shortfall_95: float
    calculated_at: datetime


class LimitStatus(BaseModel):
    metric: str
    current: float
    limit: float
    breached: bool


class StressScenarioCard(BaseModel):
    scenario: str
    shock: str
    impact: float


class StressResultRow(BaseModel):
    scenario: str
    confidence: float
    volatility: float
    var95: float
    var99: float
    es95: float


class CreditExposureRow(BaseModel):
    counterparty: str
    trades: int
    gross_mw: float
    mtm_pnl: float


@router.post("/var/calculate", response_model=APIResponse[VaRResponse])
async def var_calculate(payload: VaRRequest) -> APIResponse[VaRResponse]:
    catalog = get_settings().apex_catalog
    sql = (
        f"SELECT COALESCE(SUM(CASE WHEN upper(direction)='BUY' THEN volume_mw ELSE -volume_mw END),0) AS exposure_mw "
        f"FROM {catalog}.trading.trades"
    )
    rows = await execute_sql(sql)
    exposure = float(rows[0].get("exposure_mw", 0)) if rows else 0.0
    risk_scale = abs(exposure) * payload.spot_price * payload.volatility
    var_95 = round(risk_scale * 1.65, 2)
    var_99 = round(risk_scale * 2.33, 2)
    es_95 = round(var_95 * 1.22, 2)
    return APIResponse(
        data=VaRResponse(
            exposure_mw=round(exposure, 2),
            var_95=var_95,
            var_99=var_99,
            expected_shortfall_95=es_95,
            calculated_at=datetime.now(timezone.utc),
        ),
        region="GLOBAL",
    )


@router.get("/limits/status", response_model=APIResponse[list[LimitStatus]])
async def limits_status() -> APIResponse[list[LimitStatus]]:
    catalog = get_settings().apex_catalog
    await execute_sql(
        f"CREATE TABLE IF NOT EXISTS {catalog}.risk.limit_definitions ("
        f"metric STRING, limit_value DOUBLE)"
    )
    rows = await execute_sql(
        f"SELECT "
        f"COALESCE(SUM(ABS(volume_mw)),0) AS gross_exposure, "
        f"COALESCE(SUM(CASE WHEN upper(direction)='BUY' THEN -price*volume_mw ELSE price*volume_mw END),0) AS pnl_daily "
        f"FROM {catalog}.trading.trades"
    )
    gross_exposure = float(rows[0].get("gross_exposure", 0)) if rows else 0.0
    pnl_daily = float(rows[0].get("pnl_daily", 0)) if rows else 0.0
    pnl_drawdown = max(0.0, -pnl_daily)
    limit_rows = await execute_sql(
        f"SELECT metric, limit_value FROM {catalog}.risk.limit_definitions"
    )
    limit_map = {str(r.get("metric")): float(r.get("limit_value", 0)) for r in limit_rows}
    gross_limit = limit_map.get("Gross MW", 0.0)
    drawdown_limit = limit_map.get("Intraday Drawdown", 0.0)
    out = [
        LimitStatus(
            metric="Gross MW",
            current=round(gross_exposure, 2),
            limit=round(gross_limit, 2),
            breached=gross_limit > 0 and gross_exposure > gross_limit,
        ),
        LimitStatus(
            metric="Intraday Drawdown",
            current=round(pnl_drawdown, 2),
            limit=round(drawdown_limit, 2),
            breached=drawdown_limit > 0 and pnl_drawdown > drawdown_limit,
        ),
    ]
    return APIResponse(data=out, region="GLOBAL")


@router.get("/stress-scenarios", response_model=APIResponse[list[StressScenarioCard]])
async def stress_scenarios(
    market: str = Query(default="NEM"),
    spot_price: float = Query(default=96.0, gt=0),
    volatility: float = Query(default=0.12, gt=0),
) -> APIResponse[list[StressScenarioCard]]:
    catalog = get_settings().apex_catalog
    market_key = market.upper()
    if market_key not in {"NEM", "EPEX", "ERCOT"}:
        market_key = "NEM"
    price_union = (
        f"SELECT 'NEM' AS market, CAST(rrp AS DOUBLE) AS px FROM {catalog}.market_nem.prices "
        f"UNION ALL "
        f"SELECT 'EPEX' AS market, CAST(price_eur_mwh AS DOUBLE) AS px FROM {catalog}.market_epex.prices "
        f"UNION ALL "
        f"SELECT 'ERCOT' AS market, CAST(lmp AS DOUBLE) AS px FROM {catalog}.market_ercot.lmp"
    )
    sql = (
        f"WITH exposure AS ("
        f"  SELECT ABS(COALESCE(SUM(CASE WHEN upper(direction)='BUY' THEN volume_mw ELSE -volume_mw END),0)) AS exposure_mw "
        f"  FROM {catalog}.trading.trades WHERE upper(market)='{market_key}'"
        f"), price_stats AS ("
        f"  SELECT COALESCE(MAX(px), {spot_price}) AS max_price FROM ({price_union}) u WHERE market='{market_key}'"
        f"), base AS ("
        f"  SELECT exposure_mw, exposure_mw * {spot_price} * {volatility} AS risk_scale, max_price "
        f"  FROM exposure CROSS JOIN price_stats"
        f") "
        f"SELECT 'VaR 95%' AS scenario, CONCAT(CAST(ROUND({volatility}*100,1) AS STRING), '% vol') AS shock, ROUND(risk_scale * 1.65, 2) AS impact FROM base "
        f"UNION ALL "
        f"SELECT 'VaR 99%' AS scenario, CONCAT(CAST(ROUND({volatility}*100,1) AS STRING), '% vol') AS shock, ROUND(risk_scale * 2.33, 2) AS impact FROM base "
        f"UNION ALL "
        f"SELECT 'Expected Shortfall' AS scenario, CONCAT(CAST(ROUND({volatility}*100,1) AS STRING), '% vol') AS shock, ROUND(risk_scale * 1.65 * 1.22, 2) AS impact FROM base "
        f"UNION ALL "
        f"SELECT '{market_key} Max Price' AS scenario, 'From live strip' AS shock, ROUND(max_price * exposure_mw, 2) AS impact FROM base"
    )
    rows = await execute_sql(sql)
    out = [StressScenarioCard.model_validate(r) for r in rows]
    return APIResponse(data=out, region=market_key)


@router.get("/stress-runset", response_model=APIResponse[list[StressResultRow]])
async def stress_runset(
    market: str = Query(default="NEM"),
    spot_price: float = Query(default=96.0, gt=0),
) -> APIResponse[list[StressResultRow]]:
    catalog = get_settings().apex_catalog
    market_key = market.upper()
    if market_key not in {"NEM", "EPEX", "ERCOT"}:
        market_key = "NEM"
    sql = (
        f"WITH exposure AS ("
        f"  SELECT ABS(COALESCE(SUM(CASE WHEN upper(direction)='BUY' THEN volume_mw ELSE -volume_mw END),0)) AS exposure_mw "
        f"  FROM {catalog}.trading.trades WHERE upper(market)='{market_key}'"
        f"), scenarios AS ("
        f"  SELECT 'Base' AS scenario, 0.95 AS confidence, 0.12 AS volatility "
        f"  UNION ALL SELECT 'Volatility Shock +50%' AS scenario, 0.95 AS confidence, 0.18 AS volatility "
        f"  UNION ALL SELECT 'Tail Stress 99%' AS scenario, 0.99 AS confidence, 0.20 AS volatility"
        f"), scored AS ("
        f"  SELECT scenario, confidence, volatility, exposure_mw * {spot_price} * volatility AS risk_scale "
        f"  FROM scenarios CROSS JOIN exposure"
        f") "
        f"SELECT "
        f"  scenario, confidence, volatility, "
        f"  ROUND(risk_scale * 1.65, 2) AS var95, "
        f"  ROUND(risk_scale * 2.33, 2) AS var99, "
        f"  ROUND(risk_scale * 1.65 * 1.22, 2) AS es95 "
        f"FROM scored"
    )
    rows = await execute_sql(sql)
    out = [StressResultRow.model_validate(r) for r in rows]
    return APIResponse(data=out, region=market_key)


@router.get("/credit-exposure", response_model=APIResponse[list[CreditExposureRow]])
async def credit_exposure(market: str = Query(default="GLOBAL")) -> APIResponse[list[CreditExposureRow]]:
    catalog = get_settings().apex_catalog
    market_key = market.upper()
    where = "" if market_key == "GLOBAL" else f"WHERE upper(market)='{market_key}'"
    sql = (
        f"SELECT "
        f"  COALESCE(source_system, 'UNKNOWN') AS counterparty, "
        f"  COUNT(*) AS trades, "
        f"  COALESCE(SUM(ABS(volume_mw)), 0) AS gross_mw, "
        f"  COALESCE(SUM(CASE WHEN upper(direction)='BUY' THEN -price*volume_mw ELSE price*volume_mw END), 0) AS mtm_pnl "
        f"FROM {catalog}.trading.trades {where} "
        f"GROUP BY source_system "
        f"ORDER BY gross_mw DESC"
    )
    rows = await execute_sql(sql)
    out = [CreditExposureRow.model_validate(r) for r in rows]
    return APIResponse(data=out, region=market_key)
