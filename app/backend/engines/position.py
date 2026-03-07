from __future__ import annotations

from collections import defaultdict


def build_position_book(trades: list[dict[str, float | str]]) -> list[dict[str, float | str]]:
    positions: dict[str, float] = defaultdict(float)
    avg_price_num: dict[str, float] = defaultdict(float)
    avg_price_den: dict[str, float] = defaultdict(float)

    for t in trades:
        instrument = str(t["instrument"])
        side = str(t["side"]).upper()
        volume = float(t["volume_mw"])
        price = float(t["price"])
        signed = volume if side == "BUY" else -volume
        positions[instrument] += signed
        avg_price_num[instrument] += abs(volume) * price
        avg_price_den[instrument] += abs(volume)

    out: list[dict[str, float | str]] = []
    for instrument in sorted(positions.keys()):
        den = avg_price_den[instrument]
        out.append(
            {
                "instrument": instrument,
                "net_position_mw": round(positions[instrument], 2),
                "avg_trade_price": round(avg_price_num[instrument] / den, 2) if den else 0.0,
            }
        )
    return out
