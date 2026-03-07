from __future__ import annotations

from fastapi import APIRouter, Query

from apex_fresh.app.backend.models import APIResponse
from apex_fresh.app.backend.store import STORE

router = APIRouter(prefix="/api/v1/genie", tags=["genie"])


@router.get("/questions", response_model=APIResponse[list[str]])
def questions(
    market: str = Query(pattern="^(NEM|EPEX|ERCOT)$"),
    persona: str = Query(pattern="^(dispatch|trader|risk|quant|portfolio)$"),
) -> APIResponse[list[str]]:
    return APIResponse(data=STORE.genie_questions.get((market, persona), []))

