from __future__ import annotations

from datetime import datetime, timezone
from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.backend.apex_store import DispatchStackRecord, OfferBandRecord, STORE
from app.backend.engines.dispatch import recommend_dispatch
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


@router.post("/offer-stack", response_model=APIResponse[OfferStackResponse])
async def create_offer_stack(payload: OfferStackRequest) -> APIResponse[OfferStackResponse]:
    created_at = datetime.now(timezone.utc)
    stack = DispatchStackRecord(
        asset_id=payload.asset_id,
        scenario=payload.scenario,
        created_at=created_at,
        bands=[OfferBandRecord(**b.model_dump()) for b in payload.bands],
    )
    STORE.add_dispatch_stack(stack)
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
    latest = STORE.latest_dispatch_stack(asset_id)
    bid_price = latest.bands[0].price if latest and latest.bands else 95.0
    decision = recommend_dispatch(
        state_of_charge_pct=58.0,
        forecast_price=112.5,
        bid_price=bid_price,
        max_discharge_mw=100.0,
    )
    return APIResponse(
        data=DispatchRecommendation(asset_id=asset_id, **decision),
        region="ANZ",
    )
