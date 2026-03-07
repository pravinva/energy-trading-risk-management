from fastapi.testclient import TestClient

from app.backend.app import app


client = TestClient(app)


def test_market_summary_route() -> None:
    response = client.get("/api/v1/market/summary")
    assert response.status_code == 200
    assert response.json()["data"]["active_markets"] >= 1


def test_trade_to_position_to_risk_flow() -> None:
    create_trade = client.post(
        "/api/v1/trades/entry",
        json={
            "trader": "APEX Trader",
            "instrument": "NSW_BASE",
            "side": "BUY",
            "volume_mw": 12.5,
            "price": 96.2,
            "counterparty": "GridRetail",
        },
    )
    assert create_trade.status_code == 200
    assert create_trade.json()["data"]["status"] == "ACCEPTED"

    blotter = client.get("/api/v1/trades/blotter")
    assert blotter.status_code == 200
    assert len(blotter.json()["data"]) >= 1

    positions = client.get("/api/v1/positions/book")
    assert positions.status_code == 200
    assert isinstance(positions.json()["data"], list)

    var_result = client.post("/api/v1/risk/var/calculate", json={"confidence": 0.95, "volatility": 0.1, "spot_price": 92})
    assert var_result.status_code == 200
    assert var_result.json()["data"]["var_95"] >= 0


def test_dispatch_portfolio_and_analytics_routes() -> None:
    stack = client.post(
        "/api/v1/dispatch/offer-stack",
        json={
            "asset_id": "HORNSDALE_1",
            "scenario": "BASE",
            "bands": [
                {"band_index": 1, "price": 90, "volume_mw": 20},
                {"band_index": 2, "price": 110, "volume_mw": 30},
            ],
        },
    )
    assert stack.status_code == 200
    recommendation = client.get("/api/v1/dispatch/recommendations/HORNSDALE_1")
    assert recommendation.status_code == 200
    assert recommendation.json()["data"]["action"] in {"CHARGE", "DISCHARGE", "HOLD"}

    ppa = client.get("/api/v1/portfolio/ppa-book")
    assert ppa.status_code == 200
    assert len(ppa.json()["data"]) > 0

    models = client.get("/api/v1/analytics/model-performance")
    assert models.status_code == 200
    assert len(models.json()["data"]) > 0
