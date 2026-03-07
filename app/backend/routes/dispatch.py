from __future__ import annotations

from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.backend.config import get_settings
from app.backend.database import execute_sql
from app.backend.models import APIResponse

router = APIRouter(prefix="/api/v1/dispatch", tags=["dispatch"])


class OfferBand(BaseModel):
    band_index: int = Field(ge=1, le=10)
    price: float = Field(gt=0)
    volume_mw: float = Field(gt=0)


class OfferStackRequest(BaseModel):
    asset_id: str
    scenario: str = "BASE"
    bands: list[OfferBand]


class OfferStackResponse(BaseModel):
    asset_id: str
    scenario: str
    total_volume_mw: float
    weighted_offer_price: float
    created_at: datetime


class DispatchRecommendation(BaseModel):
    asset_id: str
    action: str
    target_mw: float
    confidence: float


class StackHistoryRow(BaseModel):
    scenario: str
    band_index: int
    price: float
    volume_mw: float
    created_at: datetime
    status: str


class LatestOfferBand(BaseModel):
    band_index: int
    price: float
    volume_mw: float


class LatestOfferStack(BaseModel):
    asset_id: str
    scenario: str
    created_at: datetime
    bands: list[LatestOfferBand]


class AcceptRecommendationRequest(BaseModel):
    asset_id: str
    action: str
    target_mw: float
    confidence: float


class AcceptRecommendationResponse(BaseModel):
    asset_id: str
    action: str
    target_mw: float
    confidence: float
    accepted_at: datetime


class DispatchAsset(BaseModel):
    asset_id: str


class DispatchServiceType(BaseModel):
    service_type: str


def _escape(value: str) -> str:
    return value.replace("'", "''")


@router.post("/offer-stack", response_model=APIResponse[OfferStackResponse])
async def create_offer_stack(payload: OfferStackRequest) -> APIResponse[OfferStackResponse]:
    created_at = datetime.now(timezone.utc)
    catalog = get_settings().apex_catalog
    await execute_sql(
        f"CREATE TABLE IF NOT EXISTS {catalog}.trading.offer_stacks ("
        f"asset_id STRING, scenario STRING, created_at TIMESTAMP)"
    )
    await execute_sql(
        f"CREATE TABLE IF NOT EXISTS {catalog}.trading.offer_bands ("
        f"asset_id STRING, scenario STRING, band_index INT, price DOUBLE, volume_mw DOUBLE, created_at TIMESTAMP)"
    )
    await execute_sql(
        f"INSERT INTO {catalog}.trading.offer_stacks VALUES "
        f"('{_escape(payload.asset_id)}', '{_escape(payload.scenario)}', TIMESTAMP '{created_at.strftime('%Y-%m-%d %H:%M:%S')}')"
    )
    if payload.bands:
        values = ", ".join(
            f"('{_escape(payload.asset_id)}', '{_escape(payload.scenario)}', {b.band_index}, {b.price}, {b.volume_mw}, TIMESTAMP '{created_at.strftime('%Y-%m-%d %H:%M:%S')}')"
            for b in payload.bands
        )
        await execute_sql(
            f"INSERT INTO {catalog}.trading.offer_bands "
            f"(asset_id, scenario, band_index, price, volume_mw, created_at) VALUES {values}"
        )
    total_volume = sum(b.volume_mw for b in payload.bands)
    weighted_price = (
        sum((b.price * b.volume_mw) for b in payload.bands) / total_volume
        if total_volume
        else 0.0
    )
    return APIResponse(
        data=OfferStackResponse(
            asset_id=payload.asset_id,
            scenario=payload.scenario,
            total_volume_mw=round(total_volume, 2),
            weighted_offer_price=round(weighted_price, 2),
            created_at=created_at,
        ),
        region="ANZ",
    )


@router.get("/recommendations/{asset_id}", response_model=APIResponse[DispatchRecommendation])
async def get_dispatch_recommendation(asset_id: str) -> APIResponse[DispatchRecommendation]:
    catalog = get_settings().apex_catalog
    await execute_sql(
        f"CREATE TABLE IF NOT EXISTS {catalog}.trading.offer_bands ("
        f"asset_id STRING, scenario STRING, band_index INT, price DOUBLE, volume_mw DOUBLE, created_at TIMESTAMP)"
    )
    sql = (
        f"WITH latest_offer AS ("
        f"  SELECT COALESCE(AVG(price), 0) AS offer_price, COALESCE(SUM(volume_mw),0) AS offer_volume "
        f"  FROM {catalog}.trading.offer_bands "
        f"  WHERE asset_id = '{_escape(asset_id)}' "
        f"    AND created_at = (SELECT MAX(created_at) FROM {catalog}.trading.offer_bands WHERE asset_id = '{_escape(asset_id)}')"
        f"), latest_market AS ("
        f"  SELECT AVG(px) AS market_price FROM ("
        f"    SELECT CAST(rrp AS DOUBLE) AS px, interval_datetime AS ts FROM {catalog}.market_nem.prices "
        f"    UNION ALL "
        f"    SELECT CAST(price_eur_mwh AS DOUBLE) AS px, delivery_datetime AS ts FROM {catalog}.market_epex.prices "
        f"    UNION ALL "
        f"    SELECT CAST(lmp AS DOUBLE) AS px, interval_datetime AS ts FROM {catalog}.market_ercot.lmp"
        f"  ) u WHERE ts >= current_timestamp() - INTERVAL 6 HOURS"
        f") "
        f"SELECT "
        f"CASE WHEN market_price > offer_price THEN 'DISCHARGE' ELSE 'CHARGE' END AS action, "
        f"CASE WHEN market_price > offer_price THEN LEAST(offer_volume, 100.0) ELSE GREATEST(offer_volume * 0.5, 10.0) END AS target_mw, "
        f"CASE WHEN market_price = 0 THEN 0.5 ELSE LEAST(0.99, GREATEST(0.5, ABS(market_price - offer_price) / market_price)) END AS confidence "
        f"FROM latest_offer CROSS JOIN latest_market"
    )
    rows = await execute_sql(sql)
    if not rows:
        raise HTTPException(status_code=404, detail=f"No recommendation available for asset {asset_id}")
    result = rows[0]
    return APIResponse(
        data=DispatchRecommendation(
            asset_id=asset_id,
            action=str(result.get("action")),
            target_mw=float(result.get("target_mw")),
            confidence=float(result.get("confidence")),
        ),
        region="ANZ",
    )


@router.get("/stack-history", response_model=APIResponse[list[StackHistoryRow]])
async def stack_history(
    asset_id: str = Query(...),
    limit: int = Query(default=30, ge=1, le=200),
) -> APIResponse[list[StackHistoryRow]]:
    catalog = get_settings().apex_catalog
    await execute_sql(
        f"CREATE TABLE IF NOT EXISTS {catalog}.trading.offer_bands ("
        f"asset_id STRING, scenario STRING, band_index INT, price DOUBLE, volume_mw DOUBLE, created_at TIMESTAMP)"
    )
    sql = (
        f"SELECT scenario, band_index, price, volume_mw, created_at, 'SUBMITTED' AS status "
        f"FROM {catalog}.trading.offer_bands "
        f"WHERE asset_id = '{_escape(asset_id)}' "
        f"ORDER BY created_at DESC, band_index ASC "
        f"LIMIT {limit}"
    )
    rows = await execute_sql(sql)
    out = [StackHistoryRow.model_validate(r) for r in rows]
    return APIResponse(data=out, region="GLOBAL")


@router.get("/offer-stack/latest", response_model=APIResponse[LatestOfferStack | None])
async def latest_offer_stack(asset_id: str = Query(...)) -> APIResponse[LatestOfferStack | None]:
    catalog = get_settings().apex_catalog
    await execute_sql(
        f"CREATE TABLE IF NOT EXISTS {catalog}.trading.offer_bands ("
        f"asset_id STRING, scenario STRING, band_index INT, price DOUBLE, volume_mw DOUBLE, created_at TIMESTAMP)"
    )
    sql = (
        f"SELECT asset_id, scenario, band_index, price, volume_mw, created_at "
        f"FROM {catalog}.trading.offer_bands "
        f"WHERE asset_id = '{_escape(asset_id)}' "
        f"  AND created_at = (SELECT MAX(created_at) FROM {catalog}.trading.offer_bands WHERE asset_id = '{_escape(asset_id)}') "
        f"ORDER BY band_index ASC"
    )
    rows = await execute_sql(sql)
    if not rows:
        return APIResponse(data=None, region="GLOBAL")
    first = rows[0]
    bands = [LatestOfferBand(band_index=int(r["band_index"]), price=float(r["price"]), volume_mw=float(r["volume_mw"])) for r in rows]
    return APIResponse(
        data=LatestOfferStack(
            asset_id=str(first["asset_id"]),
            scenario=str(first["scenario"]),
            created_at=first["created_at"],
            bands=bands,
        ),
        region="GLOBAL",
    )


@router.post("/recommendations/accept", response_model=APIResponse[AcceptRecommendationResponse])
async def accept_recommendation(payload: AcceptRecommendationRequest) -> APIResponse[AcceptRecommendationResponse]:
    catalog = get_settings().apex_catalog
    accepted_at = datetime.now(timezone.utc)
    await execute_sql(
        f"CREATE TABLE IF NOT EXISTS {catalog}.trading.dispatch_recommendations ("
        f"asset_id STRING, action STRING, target_mw DOUBLE, confidence DOUBLE, accepted_at TIMESTAMP)"
    )
    await execute_sql(
        f"INSERT INTO {catalog}.trading.dispatch_recommendations "
        f"(asset_id, action, target_mw, confidence, accepted_at) VALUES ("
        f"'{_escape(payload.asset_id)}', '{_escape(payload.action)}', {payload.target_mw}, {payload.confidence}, "
        f"TIMESTAMP '{accepted_at.strftime('%Y-%m-%d %H:%M:%S')}')"
    )
    return APIResponse(
        data=AcceptRecommendationResponse(
            asset_id=payload.asset_id,
            action=payload.action,
            target_mw=payload.target_mw,
            confidence=payload.confidence,
            accepted_at=accepted_at,
        ),
        region="GLOBAL",
    )


@router.get("/assets", response_model=APIResponse[list[DispatchAsset]])
async def dispatch_assets(market: str = Query(default="NEM")) -> APIResponse[list[DispatchAsset]]:
    catalog = get_settings().apex_catalog
    market_key = market.upper()
    await execute_sql(
        f"CREATE TABLE IF NOT EXISTS {catalog}.trading.dispatch_reference ("
        f"market STRING, asset_id STRING, service_type STRING)"
    )
    rows = await execute_sql(
        f"SELECT DISTINCT asset_id "
        f"FROM {catalog}.trading.dispatch_reference "
        f"WHERE upper(market)='{market_key}' "
        f"ORDER BY asset_id"
    )
    out = [DispatchAsset.model_validate(r) for r in rows]
    return APIResponse(data=out, region=market_key)


@router.get("/service-types", response_model=APIResponse[list[DispatchServiceType]])
async def dispatch_service_types(market: str = Query(default="NEM")) -> APIResponse[list[DispatchServiceType]]:
    catalog = get_settings().apex_catalog
    market_key = market.upper()
    await execute_sql(
        f"CREATE TABLE IF NOT EXISTS {catalog}.trading.dispatch_reference ("
        f"market STRING, asset_id STRING, service_type STRING)"
    )
    rows = await execute_sql(
        f"SELECT DISTINCT service_type "
        f"FROM {catalog}.trading.dispatch_reference "
        f"WHERE upper(market)='{market_key}' "
        f"ORDER BY service_type"
    )
    out = [DispatchServiceType.model_validate(r) for r in rows]
    return APIResponse(data=out, region=market_key)
