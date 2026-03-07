from __future__ import annotations

import math
import random


def calculate_var(
    exposure_mw: float,
    spot_price: float,
    volatility: float,
    simulations: int = 10_000,
) -> dict[str, float]:
    random.seed(7)
    pnl_distribution: list[float] = []
    for _ in range(simulations):
        shock = random.gauss(0, volatility)
        scenario_price = max(0.0, spot_price * (1 + shock))
        pnl_distribution.append((scenario_price - spot_price) * exposure_mw)

    pnl_distribution.sort()
    idx95 = max(0, int(math.floor(0.05 * simulations)) - 1)
    idx99 = max(0, int(math.floor(0.01 * simulations)) - 1)
    var95 = abs(pnl_distribution[idx95])
    var99 = abs(pnl_distribution[idx99])
    expected_shortfall95 = abs(sum(pnl_distribution[: max(1, int(0.05 * simulations))]) / max(1, int(0.05 * simulations)))
    return {
        "var_95": round(var95, 2),
        "var_99": round(var99, 2),
        "expected_shortfall_95": round(expected_shortfall95, 2),
    }
