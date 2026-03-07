from __future__ import annotations

from collections import defaultdict


def mark_to_market(side: str, volume_mw: float, trade_price: float, market_price: float) -> float:
    signed_volume = volume_mw if side.upper() == "BUY" else -volume_mw
    return round((market_price - trade_price) * signed_volume, 2)


def aggregate_pnl(rows: list[dict[str, float | str]]) -> list[dict[str, float | str]]:
    totals: dict[str, float] = defaultdict(float)
    for row in rows:
        instrument = str(row["instrument"])
        totals[instrument] += float(row["pnl"])
    return [{"instrument": k, "pnl": round(v, 2)} for k, v in sorted(totals.items())]
