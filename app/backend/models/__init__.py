from datetime import datetime, timezone
from typing import Generic, TypeVar
from pydantic import BaseModel, Field
T = TypeVar('T')

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class APIResponse(BaseModel, Generic[T]):
    data: T
    timestamp: datetime = Field(default_factory=utc_now)
    region: str | None = None

class ErrorResponse(BaseModel):
    detail: str
    code: str
    timestamp: datetime = Field(default_factory=utc_now)

class HealthResponse(BaseModel):
    status: str
    version: str
    environment: str
    lakebase_connected: bool
    timestamp: datetime = Field(default_factory=utc_now)

class UserContextResponse(BaseModel):
    email: str
    is_databricks_employee: bool
    has_gtm_access: bool
