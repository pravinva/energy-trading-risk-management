from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from threading import Lock


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class TradeRecord:
    trade_id: str
    trader: str
    instrument: str
    side: str
    volume_mw: float
    price: float
    counterparty: str
    trade_time: datetime


@dataclass(frozen=True)
class OfferBandRecord:
    band_index: int
    price: float
    volume_mw: float


@dataclass(frozen=True)
class DispatchStackRecord:
    asset_id: str
    scenario: str
    created_at: datetime
    bands: list[OfferBandRecord]


class ApexInMemoryStore:
    """Simple in-memory demo store for the APEX persona workflows."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._trades: list[TradeRecord] = []
        self._dispatch_stacks: list[DispatchStackRecord] = []

    def add_trade(self, trade: TradeRecord) -> None:
        with self._lock:
            self._trades.append(trade)

    def list_trades(self) -> list[TradeRecord]:
        with self._lock:
            return list(self._trades)

    def add_dispatch_stack(self, stack: DispatchStackRecord) -> None:
        with self._lock:
            self._dispatch_stacks.append(stack)

    def latest_dispatch_stack(self, asset_id: str) -> DispatchStackRecord | None:
        with self._lock:
            matches = [s for s in self._dispatch_stacks if s.asset_id == asset_id]
            if not matches:
                return None
            return sorted(matches, key=lambda s: s.created_at)[-1]


STORE = ApexInMemoryStore()
