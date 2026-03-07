from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from apex_fresh.app.backend.models import APIResponse

router = APIRouter(prefix="/api/v1/user", tags=["user"])


class UserContext(BaseModel):
    email: str
    market: str
    role: str


@router.get("/me", response_model=APIResponse[UserContext])
def me() -> APIResponse[UserContext]:
    return APIResponse(data=UserContext(email="demo@apex.local", market="NEM", role="trader"))

