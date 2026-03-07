from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
import random


@dataclass
class PricePoint:
    key: str
    value: Decimal
    previous: Decimal
    ts: datetime


@dataclass
class Trade:
    trade_id: str
    market: str
    instrument_id: str
    trader_id: str
    direction: str
    volume_mw: Decimal
    price: Decimal
    source_system: str
    ingested_at: datetime


@dataclass
class DispatchRecommendation:
    asset_id: str
    market: str
    recommended_mw: Decimal
    recommended_price: Decimal
    rtcb_adjusted: bool
    confidence_score: Decimal
    generated_at: datetime


@dataclass
class InMemoryStore:
    nem_prices: dict[str, PricePoint] = field(default_factory=dict)
    epex_prices: dict[str, PricePoint] = field(default_factory=dict)
    ercot_lmp: dict[str, PricePoint] = field(default_factory=dict)
    trades: list[Trade] = field(default_factory=list)
    dispatch_recs: list[DispatchRecommendation] = field(default_factory=list)
    genie_questions: dict[tuple[str, str], list[str]] = field(default_factory=dict)

    def seed(self) -> None:
        now = datetime.now(timezone.utc)
        for region, px in {"QLD1": 82, "NSW1": 94, "VIC1": 90, "SA1": 110, "TAS1": 76}.items():
            self.nem_prices[region] = PricePoint(
                key=region,
                value=Decimal(str(px)),
                previous=Decimal(str(px - random.randint(-2, 2))),
                ts=now,
            )
        for zone, px in {"DE-LU": 68, "FR": 66, "BE": 69, "NL": 71, "ES": 63}.items():
            self.epex_prices[zone] = PricePoint(
                key=zone,
                value=Decimal(str(px)),
                previous=Decimal(str(px - random.randint(-2, 2))),
                ts=now,
            )
        for node, px in {"West Hub": 46, "Houston Hub": 50, "North Hub": 43}.items():
            self.ercot_lmp[node] = PricePoint(
                key=node,
                value=Decimal(str(px)),
                previous=Decimal(str(px - random.randint(-2, 2))),
                ts=now,
            )
        self.genie_questions = {
            ("NEM", "risk"): [
                "What is our current net position in SA1 for Q1 2026?",
                "Which trader has the highest VaR utilisation today?",
            ],
            ("EPEX", "trader"): [
                "Which EPEX zone had the most negative price hours last month?",
                "Show me all trades ingested from Endur in the last 7 days",
            ],
            ("ERCOT", "dispatch"): [
                "Show BESS assets with SOC below 20% in the ERCOT fleet",
                "What is the current RTC+B signal vs day-ahead price for West Hub?",
            ],
        }


STORE = InMemoryStore()
STORE.seed()

