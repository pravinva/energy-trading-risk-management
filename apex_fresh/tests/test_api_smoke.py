from __future__ import annotations

from fastapi.testclient import TestClient

from apex_fresh.app.main import app


client = TestClient(app)


def test_health() -> None:
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    payload = res.json()["data"]
    assert payload["status"] == "ok"


def test_market_summary() -> None:
    res = client.get("/api/v1/market/summary")
    assert res.status_code == 200
    rows = res.json()["data"]
    assert len(rows) == 3


def test_risk_var_ordering() -> None:
    res = client.post("/api/v1/risk/var/calculate", json={"market": "NEM", "simulation_count": 10000})
    assert res.status_code == 200
    data = res.json()["data"]
    assert float(data["var_99"]) > float(data["var_95"])
    assert float(data["cvar_99"]) > float(data["var_99"])


def test_genie_questions() -> None:
    res = client.get("/api/v1/genie/questions?market=NEM&persona=risk")
    assert res.status_code == 200
    assert len(res.json()["data"]) >= 1

