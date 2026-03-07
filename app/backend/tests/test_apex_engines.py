from app.backend.engines.dispatch import recommend_dispatch
from app.backend.engines.pnl import mark_to_market
from app.backend.engines.position import build_position_book
from app.backend.engines.var import calculate_var


def test_mark_to_market_buy_positive_when_market_up() -> None:
    assert mark_to_market("BUY", 10, 80, 100) == 200.0


def test_build_position_book_nets_buy_sell() -> None:
    rows = build_position_book(
        [
            {"instrument": "NSW_BASE", "side": "BUY", "volume_mw": 20, "price": 95},
            {"instrument": "NSW_BASE", "side": "SELL", "volume_mw": 5, "price": 97},
        ]
    )
    assert rows[0]["net_position_mw"] == 15.0


def test_var_metrics_return_positive_values() -> None:
    out = calculate_var(exposure_mw=120, spot_price=90, volatility=0.12, simulations=1000)
    assert out["var_95"] > 0
    assert out["var_99"] > 0


def test_dispatch_recommendation_has_action() -> None:
    out = recommend_dispatch(state_of_charge_pct=50, forecast_price=120, bid_price=90, max_discharge_mw=80)
    assert out["action"] in {"CHARGE", "DISCHARGE", "HOLD"}
