from __future__ import annotations

from datetime import datetime, timezone
from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    data: T
    message: str = "ok"
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

