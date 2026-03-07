from __future__ import annotations


def recommend_dispatch(
    state_of_charge_pct: float,
    forecast_price: float,
    bid_price: float,
    max_discharge_mw: float,
) -> dict[str, float | str]:
    if state_of_charge_pct < 20:
        action = "CHARGE"
        target_mw = min(max_discharge_mw, 0.5 * max_discharge_mw)
    elif forecast_price > bid_price:
        action = "DISCHARGE"
        target_mw = max_discharge_mw
    else:
        action = "HOLD"
        target_mw = 0.0

    return {
        "action": action,
        "target_mw": round(target_mw, 2),
        "confidence": 0.82 if action != "HOLD" else 0.67,
    }
