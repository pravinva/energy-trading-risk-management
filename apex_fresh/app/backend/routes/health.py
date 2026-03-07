from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from apex_fresh.app.backend.models import APIResponse

router = APIRouter(prefix="/api/v1", tags=["health"])


class Health(BaseModel):
    status: str
    lakebase_connected: bool
    warehouse_connected: bool
    simulator_running: bool


@router.get("/health", response_model=APIResponse[Health])
def get_health() -> APIResponse[Health]:
    return APIResponse(
        data=Health(
            status="ok",
            lakebase_connected=True,
            warehouse_connected=True,
            simulator_running=True,
        )
    )

