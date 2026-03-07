from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

from fastapi import APIRouter
from pydantic import BaseModel, Field

from apex_fresh.app.backend.models import APIResponse
from apex_fresh.app.backend.store import DispatchRecommendation, STORE

router = APIRouter(prefix="/api/v1/dispatch", tags=["dispatch"])


class OfferBand(BaseModel):
    band_number: int = Field(ge=1, le=10)
    price_per_mwh: Decimal
    volume_mw: Decimal


class OfferStackDraft(BaseModel):
    asset_id: str
    market: str
    service_type: str = "ENERGY"
    bands: list[OfferBand]


class OfferStackResponse(BaseModel):
    stack_id: str
    asset_id: str
    market: str
    total_mw: Decimal
    created_at: datetime


@router.post("/{asset_id}/offer-stack", response_model=APIResponse[OfferStackResponse])
def submit_offer_stack(asset_id: str, draft: OfferStackDraft) -> APIResponse[OfferStackResponse]:
    if len(draft.bands) != 10:
        return APIResponse(
            data=OfferStackResponse(
                stack_id="INVALID",
                asset_id=asset_id,
                market=draft.market,
                total_mw=Decimal("0"),
                created_at=datetime.now(timezone.utc),
            ),
            message="expected 10 bands",
        )
    sorted_prices = [band.price_per_mwh for band in draft.bands]
    if sorted_prices != sorted(sorted_prices):
        return APIResponse(
            data=OfferStackResponse(
                stack_id="INVALID",
                asset_id=asset_id,
                market=draft.market,
                total_mw=Decimal("0"),
                created_at=datetime.now(timezone.utc),
            ),
            message="bands must be ascending by price",
        )
    total = sum((band.volume_mw for band in draft.bands), Decimal("0"))
    return APIResponse(
        data=OfferStackResponse(
            stack_id=str(uuid4()),
            asset_id=asset_id,
            market=draft.market,
            total_mw=total,
            created_at=datetime.now(timezone.utc),
        )
    )


@router.get("/{asset_id}/recommendations", response_model=APIResponse[list[dict[str, str]]])
def recommendations(asset_id: str) -> APIResponse[list[dict[str, str]]]:
    out = []
    for i in range(12):
        rec = DispatchRecommendation(
            asset_id=asset_id,
            market="ERCOT",
            recommended_mw=Decimal("180") - Decimal(i),
            recommended_price=Decimal("82") + Decimal(i) / Decimal("10"),
            rtcb_adjusted=True,
            confidence_score=Decimal("0.86"),
            generated_at=datetime.now(timezone.utc),
        )
        STORE.dispatch_recs.append(rec)
        out.append(
            {
                "interval": str(i + 1),
                "recommended_mw": str(rec.recommended_mw),
                "recommended_price": str(rec.recommended_price),
                "rtcb_adjusted": str(rec.rtcb_adjusted).lower(),
            }
        )
    return APIResponse(data=out)

